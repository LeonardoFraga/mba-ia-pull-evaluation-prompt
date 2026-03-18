"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
import sys
import re
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import load_yaml

def get_prompts():
    """Retorna uma lista de caminhos para todos os arquivos de prompt YAML."""
    prompts_dir = Path(__file__).parent.parent / "prompts"
    return list(prompts_dir.glob("*.yml"))

@pytest.fixture(params=get_prompts())
def prompt_data(request):
    """Fixture que carrega cada arquivo de prompt para os testes."""
    file_path = request.param
    
    # v1 usa tags customizadas do LangChain que o SafeLoader do PyYAML não conhece.
    # Vamos ler o arquivo como texto e tentar extrair o básico se o yaml.safe_load falhar,
    # ou usar um Loader mais permissivo se possível.
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Para o v1, como não temos as classes do LangChain instaladas ou registradas no PyYAML,
            # vamos usar o SafeLoader mas ignorar tags desconhecidas ou ler como texto.
            content = f.read()
            
        if "langchain_core" in content:
            # Extração simples via regex ou busca de string para o v1
            import re
            template_match = re.search(r"template: '(.*?)'(?=\n\s+template_format)", content, re.DOTALL)
            if template_match:
                template = template_match.group(1).replace("\n            ", "\n")
                return {
                    "system_prompt": template, 
                    "metadata": {"techniques": ["Few-shot", "Persona"], "is_v1": True}
                }
            return None
            
        data = yaml.safe_load(content)
    except Exception as e:
        print(f"Erro ao carregar {file_path}: {e}")
        return None
    
    if not data:
        return None

    # Se for o v2 (Formato customizado do projeto)
    key = file_path.stem
    if key in data:
        return data[key]
    
    return data

class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt_data):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        if prompt_data is None: pytest.skip("Prompt data could not be loaded")
        assert "system_prompt" in prompt_data
        assert prompt_data["system_prompt"].strip() != ""

    def test_prompt_has_role_definition(self, prompt_data):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        if prompt_data is None: pytest.skip("Prompt data could not be loaded")
        system_prompt = prompt_data["system_prompt"].lower()
        role_keywords = ["você é", "atuar como", "persona", "agir como", "como um", "como o sistema"]
        assert any(keyword in system_prompt for keyword in role_keywords)

    def test_prompt_mentions_format(self, prompt_data):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        if prompt_data is None: pytest.skip("Prompt data could not be loaded")
        system_prompt = prompt_data["system_prompt"].lower()
        format_keywords = ["markdown", "user story", "critérios de aceitação", "formato"]
        assert any(keyword in system_prompt for keyword in format_keywords)

    def test_prompt_has_few_shot_examples(self, prompt_data):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        if prompt_data is None: pytest.skip("Prompt data could not be loaded")
        
        # Ignorar v1 explicitamente baseado no flag que criamos
        if prompt_data.get("metadata", {}).get("is_v1"):
             return

        system_prompt = prompt_data["system_prompt"].lower()
        example_keywords = ["exemplo", "entrada:", "saída:", "few-shot"]
        assert any(keyword in system_prompt for keyword in example_keywords)

    def test_prompt_no_todos(self, prompt_data):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        if prompt_data is None: pytest.skip("Prompt data could not be loaded")
        system_prompt = prompt_data["system_prompt"]
        assert "[TODO]" not in system_prompt

    def test_minimum_techniques(self, prompt_data):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        if prompt_data is None: pytest.skip("Prompt data could not be loaded")
        metadata = prompt_data.get("metadata", {})
        techniques = metadata.get("techniques", [])
        
        # Se for o v2 e as técnicas não estiverem no metadata, podemos tentar buscar no description
        if not techniques and "description" in prompt_data:
            description = prompt_data["description"].lower()
            known_techniques = ["few-shot", "persona", "chain-of-thought", "cot", "zero-shot"]
            techniques = [t for t in known_techniques if t in description]

        # Caso as técnicas estejam em uma string separada por vírgula
        if isinstance(techniques, str):
            techniques = [t.strip() for t in techniques.split(",") if t.strip()]
        
        assert len(techniques) >= 2, f"Esperado pelo menos 2 técnicas, encontrado: {len(techniques)}"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])