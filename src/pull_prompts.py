"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from utils import save_yaml, check_env_vars, print_section_header
from langsmith import Client


load_dotenv()
client = Client()

def pull_prompts_from_langsmith():
    prompt = client.pull_prompt("leonanluppi/bug_to_user_story_v1")
    # Save the prompt locally
    save_path = Path("prompts/bug_to_user_story_v1.yml")
    save_yaml(prompt, save_path)


def main():
    """Função principal"""
    required_vars = ["LANGSMITH_API_KEY", "LANGSMITH_ENDPOINT", "LANGSMITH_PROJECT", "USERNAME_LANGSMITH_HUB"]
    check_env_vars(required_vars)
    print_section_header("Pulling Prompts from LangSmith Prompt Hub")
    pull_prompts_from_langsmith()
    print("Prompts pulled and saved to prompts/raw_prompts.yml")


if __name__ == "__main__":
    sys.exit(main())
