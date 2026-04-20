# ====================== 修复版：LCEL 管道写法（无 LLMChain，不报错） ======================
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from pydantic import SecretStr

# 1. 创建提示词模板（修改变量名，避免和类名冲突）
prompt = PromptTemplate(
    input_variables=["name"],
    template="""
    你是一个文案高手，专门为{name}设计文案，列举三个卖点
    """,
)

# 2. 大模型配置（不变）
model = ChatOpenAI(
    model="qwen-plus",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=SecretStr("sk-3b472b418a1c4d7791e8174a617325ff"),
    temperature=0.7
)

parse = StrOutputParser()
# 3. ✅ 新版核心写法：用 | 串联，替代 LLMChain
chain = prompt | model | parse

# 4. 调用（和原来用法几乎一样）
response = chain.invoke({"name": "智能手机"})

# 5. 打印结果
print(response)