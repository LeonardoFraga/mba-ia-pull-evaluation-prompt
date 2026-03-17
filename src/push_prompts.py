"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""


import sys
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header
from langsmith import Client

load_dotenv()
client = Client()


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    try:   
        print_section_header(f"Fazendo push do prompt '{prompt_name}' para o LangSmith Hub...")

        messages = [
            ("system", prompt_data["system_prompt"]),
            ("user", prompt_data["user_prompt"]),
        ]
        prompt_obj = ChatPromptTemplate.from_messages(messages)

        client.push_prompt(
            prompt_identifier=prompt_name,
            is_public=True,
            object=prompt_obj,
            tags=prompt_data.get("tags", []),
            description=prompt_data.get("description", ""),
        )


        print_section_header(f"Prompt '{prompt_name}' pushado com sucesso!")
        return True
    except Exception as e:
        print_section_header(f"Erro ao pushar prompt '{prompt_name}': {e}")
        raise e



def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    errors = []

    if not isinstance(prompt_data, dict):
        return False, ["Prompt deve ser um objeto/dict"]

    # Detecta se o YAML carregado é um mapeamento de prompts
    # Ex: { "bug_to_user_story_v1": { system_prompt: ..., user_prompt: ... } }
    is_mapping_of_prompts = any(isinstance(v, dict) for v in prompt_data.values()) and not (
        "system_prompt" in prompt_data and "user_prompt" in prompt_data
    )

    if is_mapping_of_prompts:
        for name, data in prompt_data.items():
            if not isinstance(data, dict):
                errors.append(f"'{name}' deve ser um objeto/dict")
                continue
            for field in ["system_prompt", "user_prompt"]:
                if field not in data:
                    errors.append(f"Falta '{field}' em '{name}'")
                elif not isinstance(data[field], str) or not data[field].strip():
                    errors.append(f"'{field}' em '{name}' deve ser string não vazia")

            if "description" in data and not isinstance(data["description"], str):
                errors.append(f"'description' em '{name}' deve ser string")
            if "version" in data and not isinstance(data["version"], str):
                errors.append(f"'version' em '{name}' deve ser string")
            if "tags" in data:
                if not isinstance(data["tags"], list) or not all(isinstance(t, str) for t in data["tags"]):
                    errors.append(f"'tags' em '{name}' deve ser lista de strings")

        return (len(errors) == 0, errors)

    # Caso contrário, valida um único prompt no formato antigo
    for field in ["system_prompt", "user_prompt"]:
        if field not in prompt_data:
            errors.append(f"Falta '{field}'")
        elif not isinstance(prompt_data[field], str) or not prompt_data[field].strip():
            errors.append(f"'{field}' deve ser string não vazia")

    if "description" in prompt_data and not isinstance(prompt_data["description"], str):
        errors.append("'description' deve ser string")

    if "version" in prompt_data and not isinstance(prompt_data["version"], str):
        errors.append("'version' deve ser string")

    if "tags" in prompt_data:
        if not isinstance(prompt_data["tags"], list) or not all(isinstance(t, str) for t in prompt_data["tags"]):
            errors.append("'tags' deve ser lista de strings")

    return (len(errors) == 0, errors)


def main():
    """Função principal"""
    print_section_header("Validando variáveis de ambiente...")
    required_vars = ["LANGSMITH_API_KEY", "LANGSMITH_ENDPOINT", "LANGCHAIN_PROJECT", "USERNAME_LANGSMITH_HUB"]
    check_env_vars(required_vars)
    print_section_header("Variaveis de ambiente carregadas com sucesso")

    print_section_header("Carregando prompt otimizado...")
    loaded_prompt = load_yaml("prompts/bug_to_user_story_v2.yml")
    prompt_name = "bug_to_user_story_v2"

    print_section_header(f"Validando prompt '{prompt_name}'...")
    is_valid, errors = validate_prompt(loaded_prompt)
    if not is_valid:
        print(f"Erro de validação para '{prompt_name}': {errors}")
        return False
    print_section_header(f"Prompt '{prompt_name}' validado com sucesso!")

    # Extrai o prompt correto do arquivo carregado.
    # Se o YAML for um mapeamento de prompts (ex.: { "name": { ... } }),
    # procura pela chave `prompt_name`. Caso contrário, usa `loaded_prompt` direto.
    if isinstance(loaded_prompt, dict) and prompt_name in loaded_prompt and isinstance(loaded_prompt[prompt_name], dict):
        prompt_to_push = loaded_prompt[prompt_name]
    else:
        # Se o YAML contém exatamente um prompt, use-o.
        if isinstance(loaded_prompt, dict) and len(loaded_prompt) == 1:
            prompt_to_push = next(iter(loaded_prompt.values()))
        else:
            prompt_to_push = loaded_prompt

    success = push_prompt_to_langsmith(prompt_name=prompt_name, prompt_data=prompt_to_push)
    if not success:
        print_section_header(f"Falha ao pushar prompt '{prompt_name}'. Interrompendo execução.")
        return False

    print("Prompt otimizado pushado com sucesso para o LangSmith Hub!")

    
if __name__ == "__main__":
    sys.exit(main())
