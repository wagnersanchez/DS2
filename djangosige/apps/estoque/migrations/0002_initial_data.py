# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-06-16 20:53
# Correção para versões mais recentes do Django
from __future__ import unicode_literals

import os
import json
from django.db import migrations
# Removido: from django.core.serializers import base, python  (não mais necessário para patch)
# Removido: from django.core.management import call_command (não usaremos mais loaddata diretamente)

def load_fixture(apps, schema_editor):
    """
    Carrega dados iniciais do arquivo estoque_initial_data.json manualmente,
    utilizando as versões históricas dos modelos ('apps').
    """
    # Construa o caminho para o arquivo de fixture.
    # Assume-se que o arquivo está em um diretório 'fixtures' dentro do app 'estoque'.
    # Ajuste o caminho se o seu arquivo estiver em outro lugar.
    fixture_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../fixtures'))
    fixture_filename = 'estoque_initial_data.json'
    fixture_path = os.path.join(fixture_dir, fixture_filename)

    print(f"\n  Tentando carregar dados de: {fixture_path}")

    try:
        with open(fixture_path, 'r', encoding='utf-8') as f:
            objects = json.load(f)
    except FileNotFoundError:
        print(f"  AVISO: Arquivo de fixture não encontrado em {fixture_path}. Nenhum dado inicial carregado.")
        return
    except json.JSONDecodeError:
        print(f"  ERRO: Erro ao decodificar JSON do arquivo {fixture_path}. Verifique o formato do arquivo.")
        raise # Re-levanta o erro para parar a migração

    loaded_count = 0
    skipped_count = 0
    for obj_data in objects:
        model_identifier = obj_data['model']
        fields = obj_data['fields']
        pk = obj_data.get('pk', None) # Obter a PK se existir no fixture

        try:
            # Obtém a classe do modelo histórico correto usando 'apps'
            Model = apps.get_model(model_identifier)
        except LookupError:
            print(f"  AVISO: Modelo '{model_identifier}' não encontrado no estado histórico desta migração. Pulando objeto.")
            skipped_count += 1
            continue

        # Lógica simples de criação. Pode precisar ser mais robusta
        # dependendo do seu fixture (ex: checar se já existe, lidar com relações ManyToMany).
        # Aqui, estamos assumindo que queremos criar se não existir,
        # ou apenas criar (pode falhar se a PK já existir).
        # Uma abordagem comum é usar get_or_create se a PK não for definida no fixture,
        # ou criar diretamente se a PK for definida.

        # --- Lógica de tratamento de chaves estrangeiras (exemplo) ---
        # Se houver chaves estrangeiras nos 'fields', precisamos obter
        # as instâncias relacionadas usando os modelos históricos também.
        # Exemplo: Se 'fields' tiver {'category': 1}, onde 'category' é um FK:
        # related_model_identifier = Model._meta.get_field('category').remote_field.model._meta.label_lower
        # RelatedModel = apps.get_model(related_model_identifier)
        # related_instance = RelatedModel.objects.get(pk=fields['category'])
        # fields['category'] = related_instance # Substitui o ID pela instância

        # A lógica acima para FKs é simplificada e pode precisar de ajustes.
        # Para relações ManyToMany, a complexidade é maior e geralmente
        # requer salvar o objeto principal primeiro e depois adicionar as relações.
        # ------------------------------------------------------------

        try:
            if pk is not None:
                # Se a PK está no fixture, tenta criar com essa PK
                # Ou usa update_or_create para garantir que não duplique
                obj_instance, created = Model.objects.update_or_create(
                    pk=pk,
                    defaults=fields
                )
                action = "atualizado/criado" if created else "atualizado"
            else:
                 # Se não há PK, tenta criar (pode falhar se houver unique constraints)
                 # Ou usa get_or_create baseado em algum campo único
                 # Exemplo simples: apenas cria
                 obj_instance = Model.objects.create(**fields)
                 action = "criado"

            # print(f"  Objeto {Model.__name__} (PK: {obj_instance.pk}) {action}.")
            loaded_count += 1
        except Exception as e:
            # Captura exceções durante a criação do objeto (ex: IntegrityError)
            print(f"  ERRO ao criar objeto para {Model.__name__} com dados {fields} (PK: {pk}): {e}")
            skipped_count += 1
            # Decide se quer parar a migração ou apenas pular este objeto
            # raise # Descomente para parar a migração em caso de erro

    print(f"  Carregamento de dados concluído. {loaded_count} objetos processados, {skipped_count} objetos pulados/com erro.")


class Migration(migrations.Migration):
    dependencies = [
        ('estoque', '0001_initial'),
    ]

    operations = [
        # Executa a função de carregamento manual
        migrations.RunPython(load_fixture),
    ]