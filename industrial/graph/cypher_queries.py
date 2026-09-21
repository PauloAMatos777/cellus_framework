"""Repositório central de consultas Cypher do domínio industrial.

REGRA ARQUITETURAL: nenhuma query Cypher pode existir fora deste arquivo.
"""
from __future__ import annotations

POP_EQUIPMENT = """
MATCH (p:POP {code:$pop_code})-[:UTILIZA_EQUIPAMENTO]->(e:Equipamento)
RETURN e.code AS code, e.name AS name, e.description AS description
ORDER BY e.code
"""

POP_VARIABLES = """
MATCH (p:POP {code:$pop_code})-[:MONITORA_VARIAVEL]->(v:Variavel)
OPTIONAL MATCH (v)-[:MEDIDA_EM]->(e:Equipamento)
RETURN v.tag AS tag, v.description AS description, v.unit AS unit,
       v.low_limit AS low_limit, v.high_limit AS high_limit,
       e.code AS equipment
ORDER BY v.tag
"""

POP_INSTRUMENTS = """
MATCH (p:POP {code:$pop_code})-[:UTILIZA_INSTRUMENTO]->(i:Instrumento)
OPTIONAL MATCH (i)-[:INSTALADO_EM]->(e:Equipamento)
RETURN i.tag AS tag, i.description AS description, i.measures AS measures,
       e.code AS equipment
ORDER BY i.tag
"""

POP_DECISIONS = """
MATCH (p:POP {code:$pop_code})-[:CONTEM_DECISAO]->(d:Decisao)
OPTIONAL MATCH (d)-[:AVALIA]->(v:Variavel)
RETURN d.code AS code, d.question AS question,
       collect(v.tag) AS related_tags
ORDER BY d.code
"""

POP_PREREQUISITES = """
MATCH (p:POP {code:$pop_code})-[:REQUER]->(pr:PreRequisito)
RETURN pr.description AS description ORDER BY pr.ordem
"""

POP_EXPECTED_RESULT = """
MATCH (p:POP {code:$pop_code})-[:TEM_RESULTADO]->(r:ResultadoEsperado)
RETURN r.description AS description
"""

POP_ALARMS = """
MATCH (p:POP {code:$pop_code})-[:TEM_ALARME]->(a:Alarme)
RETURN a.descricao AS descricao, a.criticidade AS criticidade
ORDER BY a.descricao
"""

VARIABLE_METADATA = """
MATCH (v:Variavel {tag:$tag})
OPTIONAL MATCH (v)-[:MEDIDA_EM]->(e:Equipamento)
OPTIONAL MATCH (v)-[:MEDIDA_POR]->(i:Instrumento)
RETURN v.tag AS tag, v.description AS description, v.unit AS unit,
       v.low_limit AS low_limit, v.high_limit AS high_limit,
       e.code AS equipment, e.name AS equipment_name,
       collect(i.tag) AS instruments
"""

EQUIPMENT_BY_VARIABLE = """
MATCH (v:Variavel {tag:$tag})-[:MEDIDA_EM]->(e:Equipamento)
RETURN e.code AS code, e.name AS name, e.description AS description
"""

INSTRUMENTS_BY_MEASUREMENT = """
MATCH (i:Instrumento)
WHERE toLower(i.measures) CONTAINS toLower($measurement)
OPTIONAL MATCH (i)-[:INSTALADO_EM]->(e:Equipamento)
RETURN i.tag AS tag, i.description AS description, i.measures AS measures,
       e.code AS equipment
"""

GRAPH_OVERVIEW = """
MATCH (pl:Planta)-[:POSSUI_AREA]->(ar:Area)-[:POSSUI_PROCESSO]->(pr:Processo)
      -[:POSSUI_POP]->(p:POP)
RETURN pl.name AS planta, ar.name AS area, pr.name AS processo,
       p.code AS pop_code, p.name AS pop_name
"""
