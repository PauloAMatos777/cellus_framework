// ===================================================================== //
//  SEED do Knowledge Graph - POP PLT-POP-A01-0001 (Partida do Processo) //
//  Neo4j = fonte unica de CONHECIMENTO (sem valores em tempo real).     //
// ===================================================================== //
MATCH (n) DETACH DELETE n;

// Hierarquia
CREATE (planta:Planta {name:'Planta A'})
CREATE (area:Area {name:'Area 01'})
CREATE (proc:Processo {name:'Processo 01'})
CREATE (pop:POP {code:'PLT-POP-A01-0001',
                 name:'Partida do Processo 01'})
CREATE (planta)-[:POSSUI_AREA]->(area)
CREATE (area)-[:POSSUI_PROCESSO]->(proc)
CREATE (proc)-[:POSSUI_POP]->(pop);

// Equipamentos
UNWIND [
  ['EQ-P01','Bomba de diluicao','Bomba de fluido de diluicao'],
  ['EQ-P02','Transportador de alimentacao','Rosca de alimentacao do processo'],
  ['EQ-P03','Prensa desaguadora','Prensa de desaguamento do produto'],
  ['EQ-P04','Prensa A','Prensa de processamento A'],
  ['EQ-P05','Prensa B','Prensa de processamento B'],
  ['EQ-P06','Filtro','Filtro lavador do produto'],
  ['EQ-R01','Reator','Reator principal do processo'],
  ['EQ-P07','Bomba de transferencia','Bomba de transferencia de produto'],
  ['EQ-P08','Transportador de saida','Rosca transportadora de saida'],
  ['EQ-M01','Misturador','Misturador de insumos quimicos']
] AS e
MATCH (pop:POP {code:'PLT-POP-A01-0001'})
CREATE (eq:Equipamento {code:e[0], name:e[1], description:e[2]})
CREATE (pop)-[:UTILIZA_EQUIPAMENTO]->(eq);

// Variaveis (metadados: tag, descricao, unidade, limites, equipamento)
UNWIND [
  ['FT-001','Vazao de fluido de diluicao','m3/h',100.0,200.0,'EQ-P01'],
  ['FT-002','Setpoint vazao filtro A','m3/h',40.0,90.0,'EQ-P06'],
  ['FT-003','Setpoint vazao filtro B','m3/h',40.0,90.0,'EQ-P06'],
  ['AT-001','Consistencia real do produto','%',3.5,5.5,'EQ-P03'],
  ['AT-002','Indice de qualidade (analisador)','un',8.0,14.0,'EQ-R01'],
  ['PT-001','Pressao do reator','bar',4.0,10.0,'EQ-R01'],
  ['TT-001','Temperatura do reator','degC',70.0,95.0,'EQ-R01'],
  ['CT-001','Controle de consistencia entrada','%',3.5,5.5,'EQ-M01'],
  ['WT-001','Torque/carga prensa A','%',0.0,95.0,'EQ-P04'],
  ['ST-001','Velocidade/consistencia prensa A','%',30.0,80.0,'EQ-P04'],
  ['WT-002','Torque/carga prensa B','%',0.0,95.0,'EQ-P05'],
  ['ST-002','Velocidade/consistencia prensa B','%',30.0,80.0,'EQ-P05']
] AS v
MATCH (pop:POP {code:'PLT-POP-A01-0001'}), (eq:Equipamento {code:v[5]})
CREATE (var:Variavel {tag:v[0], description:v[1], unit:v[2],
                      low_limit:toFloat(v[3]), high_limit:toFloat(v[4])})
CREATE (pop)-[:MONITORA_VARIAVEL]->(var)
CREATE (var)-[:MEDIDA_EM]->(eq);

// Instrumentos
UNWIND [
  ['WT-002','Indicador de torque prensa B','Torque/Carga','EQ-P05'],
  ['WT-001','Indicador de torque prensa A','Torque/Carga','EQ-P04'],
  ['CT-002','Controlador de consistencia B','Consistencia','EQ-P05'],
  ['ST-001','Controlador velocidade/consistencia A','Velocidade','EQ-P04'],
  ['PT-001','Controlador de pressao do reator','Pressao','EQ-R01'],
  ['TT-001','Controlador de temperatura do reator','Temperatura','EQ-R01'],
  ['AT-002','Analisador de indice de qualidade','Indice de Qualidade','EQ-R01']
] AS i
MATCH (pop:POP {code:'PLT-POP-A01-0001'}), (eq:Equipamento {code:i[3]})
CREATE (inst:Instrumento {tag:i[0], description:i[1], measures:i[2]})
CREATE (pop)-[:UTILIZA_INSTRUMENTO]->(inst)
CREATE (inst)-[:INSTALADO_EM]->(eq);

// Instrumento -> Variavel que mede (quando a tag coincide)
MATCH (i:Instrumento), (v:Variavel) WHERE i.tag = v.tag
CREATE (v)-[:MEDIDA_POR]->(i);

// Decisoes (com vinculo as variaveis que as validam)
UNWIND [
  ['D-001','Sinal de torque esta em 100%?',['WT-001','WT-002']],
  ['D-002','Consistencia entre 3.5 e 5.5%?',['AT-001','CT-001']],
  ['D-003','Produto em toda extensao da prensa?',['ST-001']],
  ['D-004','Filtro EQ-P06 pegou carga?',['FT-002','FT-003']],
  ['D-005','Variaveis dentro dos parametros?',['PT-001','TT-001']]
] AS d
MATCH (pop:POP {code:'PLT-POP-A01-0001'})
CREATE (dec:Decisao {code:d[0], question:d[1]})
CREATE (pop)-[:CONTEM_DECISAO]->(dec)
WITH dec, d[2] AS tags
UNWIND tags AS t
MATCH (v:Variavel {tag:t})
CREATE (dec)-[:AVALIA]->(v);

// Pre-requisitos
UNWIND [
  [1,'Processo em operacao'],
  [2,'Estoque de materia-prima suficiente'],
  [3,'Disponibilidade de fluido de selagem'],
  [4,'Disponibilidade de vapor'],
  [5,'Disponibilidade de fluido de diluicao']
] AS pr
MATCH (pop:POP {code:'PLT-POP-A01-0001'})
CREATE (p:PreRequisito {ordem:pr[0], description:pr[1]})
CREATE (pop)-[:REQUER]->(p);

// Alarmes do procedimento (definicao - o "ativo" vem do MCP)
UNWIND [
  ['Torque alto na prensa','ALTA'],
  ['Consistencia fora da faixa','ALTA'],
  ['Filtro sem carga','MEDIA'],
  ['Pressao do reator fora da faixa','ALTA'],
  ['Temperatura do reator fora da faixa','ALTA']
] AS a
MATCH (pop:POP {code:'PLT-POP-A01-0001'})
CREATE (al:Alarme {descricao:a[0], criticidade:a[1]})
CREATE (pop)-[:TEM_ALARME]->(al);

// Resultado esperado
MATCH (pop:POP {code:'PLT-POP-A01-0001'})
CREATE (r:ResultadoEsperado {description:
  'Partida do processo realizada atendendo qualidade, seguranca e meio ambiente.'})
CREATE (pop)-[:TEM_RESULTADO]->(r);
