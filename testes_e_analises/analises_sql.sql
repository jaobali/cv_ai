SELECT
id_curriculo,
resumo_llm_custo_chamada_USD * 6 as resumo_llm_custo_chamada_reais,
opiniao_llm_custo_chamada_USD * 6 as opiniao_llm_custo_chamada_reais,
score_llm_custo_chamada_USD * 6 as score_llm_custo_chamada_reais,
(resumo_llm_custo_chamada_USD + opiniao_llm_custo_chamada_USD + score_llm_custo_chamada_USD) * 6 as custo_total_reais
from curriculos;

---------------------------------

SELECT
    AVG((resumo_llm_custo_chamada_USD + opiniao_llm_custo_chamada_USD + score_llm_custo_chamada_USD) * 6) AS media_custo_total
FROM curriculos;

----------------------------------

SELECT
id_curriculo,
md_time_execution / (md_time_execution + resumo_llm_time_execution + opiniao_llm_time_execution + score_llm_time_execution) as percent_md_time_execution,
resumo_llm_time_execution / (md_time_execution + resumo_llm_time_execution + opiniao_llm_time_execution + score_llm_time_execution) as percent_resumo_llm_time_execution,
opiniao_llm_time_execution / (md_time_execution + resumo_llm_time_execution + opiniao_llm_time_execution + score_llm_time_execution) as percent_opiniao_llm_time_execution,
score_llm_time_execution / (md_time_execution + resumo_llm_time_execution + opiniao_llm_time_execution + score_llm_time_execution) as percent_score_llm_time_execution,
md_time_execution + resumo_llm_time_execution + opiniao_llm_time_execution + score_llm_time_execution as tempo_total
from curriculos;

----------------------------------

SELECT
    AVG(md_time_execution + resumo_llm_time_execution + opiniao_llm_time_execution + score_llm_time_execution) AS tempo_medio
FROM curriculos;








