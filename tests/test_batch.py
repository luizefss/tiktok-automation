import sys
sys.path.append('.')
from content_generator import ContentGenerator

def test_batch_generation():
    """Teste geração em lote com diferentes IAs"""
    
    generator = ContentGenerator()
    
    print("🎬 TESTE: Geração em lote (3 roteiros)")
    print("=" * 50)
    
    roteiros = generator.gerar_batch_roteiros(quantidade=3)
    
    print(f"\n📊 RESULTADO FINAL:")
    print(f"✅ Gerados: {len(roteiros)}/3")
    
    for i, roteiro in enumerate(roteiros, 1):
        print(f"�� {i}. {roteiro['titulo']}")
        print(f"   📂 Categoria: {roteiro['categoria']}")
        print(f"   🎯 Hook: {roteiro['hook'][:50]}...")
        print()
    
    return roteiros

if __name__ == "__main__":
    roteiros = test_batch_generation()
