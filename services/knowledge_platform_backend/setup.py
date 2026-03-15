from setuptools import setup, find_packages

setup(
    name="knowledge_platform_backend",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "requests",
        "python-dotenv",
        "langchain-core",
        "langchain-community",
        "langchain-openai",
        "langchain-chroma",
        "pydantic-settings",
        "markdownify",
        "scikit-learn",
        "jieba",
        "unstructured",
        "markdown",
        "omegaconf>=2.3.0",
        "pyyaml",  # OmegaConf 底层依赖 yaml，最好显式声明
    ],
)