import json
import os
from collections import defaultdict


def parse_swagger(json_file):
    with open(json_file, 'r') as f:
        swagger_data = json.load(f)

    endpoints_by_tag = defaultdict(list)
    components = swagger_data.get('components', {}).get('schemas', {})

    for path, methods in swagger_data['paths'].items():
        for method, details in methods.items():
            # 提取接口的标签（默认归类到 "default"）
            tags = details.get('tags', ['default'])
            for tag in tags:
                endpoint = {
                    'path': path,
                    'method': method.upper(),
                    'parameters': details.get('parameters', []),
                    'requestBody': details.get('requestBody'),
                    'responses': details['responses'],
                    'summary': details.get('summary', '')
                }
                endpoints_by_tag[tag].append(endpoint)

    return endpoints_by_tag, components
def resolve_schema(ref, components):
    """解析 $ref 引用（如 #/components/schemas/User）"""
    if ref.startswith('#/components/schemas/'):
        schema_name = ref.split('/')[-1]
        return components.get(schema_name, {})
    return {}

def generate_example_data(schema, components):
    """根据 Schema 生成示例数据（支持嵌套）"""
    example = {}
    if 'properties' in schema:
        for prop, prop_schema in schema['properties'].items():
            if '$ref' in prop_schema:
                ref_schema = resolve_schema(prop_schema['$ref'], components)
                example[prop] = generate_example_data(ref_schema, components)
            else:
                # 根据类型生成默认值
                prop_type = prop_schema.get('type', 'string')
                example[prop] = {
                    'string': 'sample_string',
                    'integer': 123,
                    'boolean': True,
                    'array': [{'item': 'sample_item'}]
                }.get(prop_type, 'unknown')
    return example


def generate_features(endpoints_by_tag, components, output_dir="features"):
    for tag, endpoints in endpoints_by_tag.items():
        feature_file = f"{output_dir}/{tag.replace(' ', '_')}.feature"
        #如果feature_file不存在则创建该文件和文件夹
        if not os.path.exists(feature_file):
            os.makedirs(os.path.dirname(feature_file), exist_ok=True)
        with open(feature_file, 'w') as f:
            f.write(f"Feature: {tag} 接口测试\n\n")
            for endpoint in endpoints:
                f.write(f"  Scenario: {endpoint['summary']}\n")

                # 处理路径参数和查询参数
                for param in endpoint['parameters']:
                    if param['in'] == 'path':
                        f.write(f"    Given 设置路径参数 {param['name']} 为 1\n")
                    elif param['in'] == 'query':
                        f.write(f"    Given 设置查询参数 {param['name']} 为 test\n")

                # 处理请求体（解析 Schema）
                if endpoint['requestBody']:
                    content = endpoint['requestBody'].get('content', {})
                    for media_type, media_info in content.items():
                        if '$ref' in media_info.get('schema', {}):
                            ref = media_info['schema']['$ref']
                            schema = resolve_schema(ref, components)
                            example_data = generate_example_data(schema, components)
                            f.write(f"    Given 设置请求体为:\n")
                            f.write(f"      \"\"\"\n")
                            f.write(f"      {json.dumps(example_data, indent=2)}\n")
                            f.write(f"      \"\"\"\n")

                # 发送请求
                f.write(f"    When 发送 {endpoint['method']} 请求到 \"{endpoint['path']}\"\n")

                # 根据响应 Schema 生成断言
                success_response = next(
                    (resp for code, resp in endpoint['responses'].items() if code.startswith('2')),
                    None
                )
                if success_response:
                    response_schema = success_response.get('content', {}).get('application/json', {}).get('schema')
                    if response_schema and '$ref' in response_schema:
                        ref = response_schema['$ref']
                        schema = resolve_schema(ref, components)
                        example_data = generate_example_data(schema, components)
                        for field in schema.get('properties', {}).keys():
                            f.write(f"    Then 响应体中 \"{field}\" 字段应存在\n")
                            f.write(
                                f"    And 响应体中 \"{field}\" 的类型应为 \"{schema['properties'][field].get('type')}\"\n")
    print("Feature 文件生成完毕！")

endpoints_by_tag, components = parse_swagger("/Users/m661557/Downloads/HCN2.0服务-辖区服务_OpenAPI.json")
generate_features(endpoints_by_tag, components, output_dir="features")