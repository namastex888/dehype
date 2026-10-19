<a id="methodology"></a>
# Metodologia

Método de descoberta atual: **3.0**; o histórico **2.0** continua executável com sua configuração congelada. Código: [scoring.py](scoring.py); parâmetros: [scoring_config.json](scoring_config.json). A página renderiza `web/METHODOLOGY.md`, uma cópia idêntica; o texto em português é [METHODOLOGY.pt.md](METHODOLOGY.pt.md), copiado para `web/METHODOLOGY.pt.md` da mesma forma, com as mesmas seções e âncoras. Os números seguem a notação do original em inglês: ponto como separador decimal e vírgula como separador de milhar.

<a id="overview"></a>
## Visão geral

O rastreador ranqueia três coisas:

- **Artigos**: artigos do arXiv / Hugging Face sobre agentes de IA, harnesses e camadas de contexto, JEPA, JEV (modelos de decisão), modelos de mundo e de ação, e alguns paradigmas não-LLM.
- **GitHub**: repositórios ranqueados por um *índice de descoberta por atividade* multissinal. O nome histórico “índice de confiança” não atesta que o código seja confiável.
- **HYPE**: proxies (indicadores indiretos) amostrados de **Atenção** (Attention) e **Descoberta** (Discovery) para projetos abertos e fechados, com famílias de uso separadas, cada uma com fonte. Nenhuma das duas pontuações mede capacidade técnica, validação econômica ou verdade.

As pontuações são proxies de descoberta de 0-100. Elas compartilham as etapas de sinal ponderado e de cobertura, mas o encolhimento final difere:

```
1. normalise each present signal:   u = min(1, log1p(v) / log1p(P95_ref))      (0 stays 0)
2. raw score:                       raw = 100 * sum(w_k * u_k) / sum(w_k)       over PRESENT signals
3. evidence coverage:               c = sum(w_k * e_k over present) / sum(w_k over all signals)
4. anti-noise multipliers:          raw = raw * m_1 * m_2 * ...                 (see Anti-noise rules)
5. GitHub/Papers:                   score = prior + c * (raw - prior)
                                   prior = median raw score of the reference population
   HYPE Attention/Discovery:       score = 50 + c * (pct - 50)
                                   pct = mid-rank percentile of raw, not raw itself
```

A Atenção do HYPE ranqueia as pontuações brutas entre os candidatos de posts amostrados da janela; a Descoberta do HYPE ranqueia dentro da coorte com proxies disponíveis. Ambas encolhem o percentil em direção a um prior (valor a priori) fixo e neutro de 50, não a uma mediana de referência. As seções detalhadas abaixo definem os sinais, as referências e as heurísticas.

**Ausente continua ausente**: `null`, exibido como —. Sem sinal, sem pontuação. Uma métrica de usuários/clientes de um produto fechado que não foi observada não é zero nem evidência de baixo valor; o zero observado continua sendo um valor medido distinto.

<a id="data-sources-and-their-limits"></a>
## Fontes de dados e seus limites

| Fonte | O que coletamos | Limites |
|---|---|---|
| API do arXiv | artigos que correspondem a consultas por palavra-chave em cada assunto | só recupera o que as palavras-chave alcançam; a API aplica limite de taxa (HTTP 429), e nesse caso o último resultado em cache é reutilizado e a falha aparece em "Data sources" (Fontes de dados) |
| API de artigos do Hugging Face | upvotes, repositório GitHub vinculado, estrelas do repositório, laboratório | upvotes só existem para artigos publicados no HF; cache de 6-72 h conforme a idade do artigo |
| Hacker News (Algolia) | histórias e comentários que contêm o id exato do arXiv | só HN; a API JSON do Reddit é bloqueada sem autenticação, e X/LinkedIn não têm API gratuita |
| API REST do GitHub | busca de repositórios, issues / PRs / commits numa janela retroativa de 30 dias (Search API), contagens de contribuidores | a cota da Search API limita quantos repositórios recebem dados de atividade por execução (100 com autenticação, 30 sem); o endpoint de timestamps de stargazers retornou HTTP 404 nas nossas execuções, então o crescimento de estrelas vem dos nossos próprios snapshots |
| Dossiê de pesquisa social (só HYPE) | posts amostrados, autores únicos, plataformas, números de uso com fonte, sinais céticos | uma amostra intencional de fontes públicas, não uma escuta exaustiva. O HN responde por cerca de 2,019 dos 2,163 posts amostrados. Não há série de crescimento, então a aceleração não pode ser medida. Não é incluído no repositório |

Toda falha de fonte recorre, como alternativa, ao último payload válido em cache e é registrada em `data.json["sources"]`.

<a id="x-route-and-public-data"></a>
## Rota do X e dados públicos

Rota do X: as contagens do X, e as pontuações de atenção calculadas a partir de posts do X, vêm da rodada de pesquisa de 2026-10-07, cujas notas citam relatórios "x_search" e leituras via "X syndication". Não está registrado se essas são interfaces publicadas pelo X, nem se alguma chamada paga foi feita. Uma contagem do X é um número de posts na nossa amostra, nunca alcance; nenhum texto de post, link de post ou número do X é mostrado (fica apenas o link do perfil do próprio projeto no X).

Os arquivos públicos (`pulse.json`, `briefing.json`, `hype.json`) não trazem nenhum handle de pessoa: autores das redes de conversa, URLs de posts que nomeiam a conta e os campos de conta do dossiê ficam de fora. Posts do Reddit, X, LinkedIn, YouTube, Telegram e Discord aparecem só como contagem, sem título, autor, link ou pontuação; um post do Mastodon é uma contagem, a menos que seu link do mastodon.social sem handle tenha passado numa verificação de renderização sem login menos de 7 dias antes da build. `scripts/check_page.mjs` reprova a build em qualquer um desses casos.

Manchetes e títulos de posts aparecem como foram publicados, no idioma original, e nunca são traduzidos. Cada um traz uma tag `lang` tirada dos metadados da própria fonte (o `language` do status do Mastodon, a primeira entrada de `langs` do Bluesky, o `<language>` do RSS ou o `xml:lang` do Atom do feed); sem isso, `und` (indeterminado). Hacker News, Lobsters, Reddit, arXiv, GitHub e o dossiê de pesquisa não publicam idioma, então seus títulos ficam `und`. Uma manchete que é o rótulo de um tópico fica `und`; a linha fixa `<network> discussion, title not shown` é texto nosso. Tudo o que escrevemos tem uma entrada em inglês e outra em português em [web/i18n/strings.json](web/i18n/strings.json).

Nos dados de 2026-10-16, remover os handles e o conteúdo do X, LinkedIn, YouTube e Telegram do dossiê de pesquisa mudou as vozes dos tópicos em 30 dias em -0.2% (29 de 157 tópicos; 13 tópicos de projeto ganharam uma voz quando seus posts do X foram atribuídos a eles), o peso em -3.5% e o sinal em 1.7 ponto em média em 133 tópicos; as vozes e o peso em 7 dias não mudaram. O efeito acaba quando os posts do dossiê, datados até 2026-10-07, saírem da janela de 30 dias (por volta de 2026-11-06).

Medido uma vez, no banco da execução de refresh 38948143514 (artefato `history-38948143514`, os dados de 2026-10-16), com `python3 pulse.py --offline` rodado antes e depois da limpeza (scrub), no mesmo banco.

<a id="normalization"></a>
## Normalização

A versão 1 dividia pelo máximo da janela. A normalização de descoberta da v2 continua na v3 para sinais proxy compatíveis:

```
P95_ref = 95th percentile of the positive values of that signal across ALL tracked items in this run
u(v)    = 0                               if v = 0
        = min(1, log1p(v) / log1p(P95_ref))   otherwise
```

- A referência não depende da janela. O GitHub usa os valores de 30 dias de cada repositório; os artigos usam todos os artigos rastreados. Uma janela de 1 dia com 8 candidatos é pontuada na mesma escala que a lista completa.
- Valores acima do P95 são winsorizados para 1, então um item viral só limita o próprio valor.
- Uma fração de PRs só é usada com uma coorte observada e compatível de PRs criados e mergeados, nunca como uma razão truncada de eventos não relacionados.
- Se houver menos de `min_reference` (5) valores positivos, usa-se o máximo.
- `normalization.method = "percentile"` passa a usar percentis baseados em posto (posto médio entre os valores positivos de referência), para quem quiser testar isso em `eval.py`.

<a id="evidence-coverage-and-shrinkage"></a>
## Cobertura de evidência e encolhimento

**Cobertura de evidência** é a completude ponderada dos sinais, com descontos heurísticos. Não é verificação, cobertura amostral global, confiança na verdade nem acurácia calibrada:

```
c = sum(w_k * e_k for present signals) / sum(w_k for all signals)
e_k = 1    measured value
e_k = 0.5  rate proxy (per-day-since-release average used because no earlier snapshot exists)
e_k = 0.5  stars-only evidence for a paper's linked repo (no activity data)
e_k = c_repo  linked repository evidence coverage
Usage vendor claims are displayed separately, not discounted into a composite user magnitude.
```

O **encolhimento de GitHub/Artigos** é uma heurística em direção à pontuação bruta mediana de referência. Não tem uma interpretação probabilística bayesiana validada:

```
score = prior + c * (raw - prior)
prior = median raw score of the reference population in this run
        (all repos at 30d for GitHub, all tracked papers for Papers)
```

Uma linha de GitHub/Artigos com 25% de cobertura percorre um quarto do caminho entre o prior de referência e seu valor bruto. Para prior 30 e bruto 95, isso dá `30 + 0.25 * 65 = 46.3`. Já o HYPE parte do prior fixo 50 em direção ao seu percentil, conforme definido nas seções de Atenção e Descoberta. Os tooltips mostram o valor bruto, a cobertura e o prior, separados das dimensões não qualificadas.

Toda linha atual também expõe `verification: null`, `freshness: {assessed_at: null, newest_evidence_at: null}` e `independence: {origin_ids: [], rationale: null}`. Esses campos estão não qualificados; não são achados negativos. Contagens, um número observado pela plataforma, um rótulo de fornecedor, o horário de geração do cache ou vários sites não conseguem estabelecer replicação independente, os relógios das fontes nem independência de origem comum. Essas projeções de descoberta não são registros `Assessment.confidence`: esse contrato exige contagens de coorte de evidência admitida e qualificação de proveniência, que este pipeline não obteve.

<a id="papers-score"></a>
## Pontuação de artigos

```
signals (weight):  upvotes   HF upvote momentum            0.40
                   code      linked-repo activity / 100     0.35   (evidence = repo coverage)
                   mentions  HN mention momentum            0.25
```

- **Momentum de upvotes / menções** = delta real entre dois dos nossos snapshots (veja Momentum). Sem um snapshot anterior, é `value / max(age_days, 1)`: rotulado *since-release* (desde a publicação) quando o artigo tem menos de 7 dias (essa média cobre a vida inteira dele); caso contrário, *rate-proxy* (metade da evidência, `~` na página).
- **Código**: o índice de descoberta por atividade do repositório vinculado. Sem atividade rastreada, o momentum de estrelas do repositório vinculado conta como evidência com metade do peso; caso contrário, fica ausente. Disponibilidade/popularidade do código não é correção funcional nem capacidade.
- **Regra de poucos votos**: a evidência de upvotes é multiplicada por `n / (n + 10)`, onde n é a contagem de upvotes do artigo (`papers.upvote_evidence_k`). Um artigo com um dia de vida e 6 votos pode ter a maior taxa de upvotes do corpus. É uma amostra pequena, então conta como 0.38 de um sinal e a pontuação é encolhida em direção ao prior. Artigos com menos de 10 votos recebem a marcação `few-votes`. Sem essa regra, artigos recentes empatavam no topo da escala de upvotes e se reembaralhavam a cada execução.
- **Regra de post único**: se a atenção de um artigo no HN é exatamente um post ou comentário, o sinal de menções é multiplicado por 0.5.
- As janelas filtram os artigos pela data de publicação. A pontuação em si não depende da janela.

<a id="repo-trust-index"></a>
## Índice de confiança de repositórios

```
signals (weight):  stars           star growth / day                      0.25
                   issues          (issues opened + closed) / 30 days     0.15
                   prs             PRs opened / 30 days                   0.10
                   merge           merged among PRs created in cohort     0.10
                   commits         commits / 30 days                      0.15
                   contribs        contributor count (level)              0.10
                   contrib_growth  contributors gained / day              0.15
```

- A atividade (issues, PRs, taxa de merge, commits) usa uma janela retroativa de 30 dias e só entra em janelas de 15 dias ou mais (`activity_min_window_days`). Janelas curtas não fingem que uma média de 30 dias é uma contagem de 1 dia.
- **Correção da coorte de PRs**: denominador = PRs com `created:>since`; numerador = esses mesmos PRs que satisfazem `is:merged`. A contagem separada `merged:>since` é volume de eventos e pode incluir PRs mais antigos. Dez criados, quatro deles mergeados, e vinte eventos de merge dão **4/10 = 0.4**, não 20/10 truncado em 1. Contagens de interseção vazias, indisponíveis ou inválidas dão `null`. Caches/fixtures legados sem a interseção não conseguem reconstruí-la, então a pontuação atual omite esse sinal. As chamadas de busca não são atômicas; contagens inconsistentes continuam ausentes, e não são corrigidas por palpite.
- **Crescimento de estrelas**, em ordem de preferência: o repositório nasceu dentro da janela (todas as suas estrelas são crescimento dentro da janela), ou timestamps exatos de stargazers quando o GitHub os fornece, ou um delta real entre nossos snapshots. Como último recurso, `stars / age`, marcado *rate-proxy*, com metade da evidência.
- Totais de estrelas acumulados ao longo da vida nunca são um sinal.
- `cache/repo_trust.json` mantém o nome de arquivo histórico, mas os campos atuais são `trust` (índice de descoberta por atividade) e `coverage`. Artigos e HYPE consomem esse proxy de atividade, com esse nome, e não um veredito de segurança de código. Caches antigos sem a cobertura atual não entram no produtor atual do HYPE.
- Janelas: um repositório é candidato quando foi criado ou recebeu push dentro da janela.

<a id="momentum"></a>
## Momentum

Quando existem pelo menos dois snapshots de um item (banco de histórico: `paper_snap`, `repo_snap`), o crescimento é um **delta real**:

```
rate = max(0, value_now - value_then) / span_days
then = the earlier snapshot closest to (now - horizon), at least min_snapshot_span_days (0.5) old
horizon = the window length for repos (90 for "overall"), 7 days for papers
```

Isso se aplica a estrelas e contribuidores (repositórios) e a upvotes, menções no HN e estrelas do repositório vinculado (artigos).

Um delta num intervalo muito mais curto que o horizonte é, em grande parte, ruído. Por isso, quando nossos snapshots cobrem só parte do horizonte, a taxa é **combinada** (blended) com a taxa por dia desde a publicação, na proporção da cobertura:

```
w    = min(1, span_days / horizon)
rate = w * delta_rate + (1 - w) * since_release_rate        (kind: "blended")
evidence = 0.5 + 0.5 * w                                     (0.5 = rate_proxy_evidence)
```

Sem histórico anterior, usa-se a taxa por dia desde a publicação, marcada **rate-proxy** (metade da evidência). Artigos jovens usam a taxa de toda a sua vida como *since-release*. A extensão do histórico é específica da execução arquivada; o horário de geração não prova que toda medição de fonte esteja atualizada.

<a id="anti-noise-rules"></a>
## Regras antirruído

| Regra | Aplica-se a | Efeito |
|---|---|---|
| Pico de estrelas sem atividade correspondente (padrão de fazenda de estrelas) | repositórios | a unidade de estrelas é limitada a `max(issues, PRs, commits units) + 0.4`; marcação `stars>activity` |
| Estrelas, mas nenhum contribuidor externo | repositórios com unidade de estrelas >= 0.5 e <= 1 contribuidor | bruto x 0.8; marcação `solo` |
| Persistência acima de picos isolados | repositórios com contagens exatas de estrelas em pelo menos 2 dos horizontes de 7/30/90 dias | `s = min(rate_h) / max(rate_h)`, bruto x (1 - 0.15 * (1 - s)); marcação `spike` se s < 0.25 |
| Atenção de post único | artigos cuja atenção no HN é um post | unidade de menções x 0.5; marcação `single-post` |
| Atenção em uma única plataforma | HYPE | bruto do Hype x 0.8; marcação `single-platform` |
| Um punhado de autores | linhas do HYPE com <= 3 vozes únicas | bruto do Hype x 0.8; marcação `few-voices` |

As marcações aparecem ao lado do item na página. A persistência exige contagens exatas por horizonte. Deltas de snapshots dão a mesma taxa para todos os horizontes, então não são tratados como evidência de persistência.

<a id="movement-arrows"></a>
## Setas de movimento

- As posições são comparadas **apenas entre itens presentes nas duas execuções** da mesma aba, janela e visão. Um item que entra na lista não faz todos os outros ganharem uma seta para baixo.
- Um item que não estava na lista anterior mostra **new** (novo). Se menos de 50% das linhas coincidirem com as da execução anterior (`min_overlap`), todas as linhas mostram *new*, com o motivo no tooltip.
- **Histerese**: uma seta só aparece se a posição entre os itens em comum mudou pelo menos 2 **e** a pontuação mudou pelo menos 1.0 ponto. Caso contrário, a linha mostra `=`.
- Quando a versão da pontuação muda, o movimento é zerado (`·`), porque pontuações de dois algoritmos não são comparáveis.

<a id="hype-attention-score"></a>
## HYPE: Pontuação de atenção

Por janela (1d / 7d / 30d / 90d, conforme medido pela pesquisa; *overall* (geral) = a janela retroativa de 12 meses):

```
velocity      sampled posts in window / effective days    0.35   effective days = max(1, min(window, days since first seen))
acceleration  growth of velocity                           0.25   MISSING: the research has no growth series
voices        sampled unique authors in window             0.20
spread        (platforms with posts - 1) / (4 - 1), cap 1  0.20   fixed scale: one platform = 0, four or more = 1
```

Velocidade e vozes usam a referência de candidatos da janela. As penalidades por plataforma/voz são heurísticas, não prova de coordenação. A atenção é um percentil entre os projetos com posts amostrados:

```
pct   = mid-rank percentile of the raw score among the window's candidates (0..100)
Attention = 50 + c * (pct - 50)       (50 is the fixed neutral prior)
```

A aceleração não é observada, então a cobertura da atenção é no máximo 0.75. Este é um **proxy (indicador indireto) de atenção amostrado**, não uma contagem de toda a plataforma, uma população de usuários nem uma medida de validação.

<a id="hype-discovery-score"></a>
## HYPE: Pontuação de descoberta

Componentes de descoberta independentes de janela:

```
gh_trust    linked GitHub activity index / 100       0.30   evidence = linked repo coverage
paper       HF upvotes                              0.20   paper attention, not capability
discussion  sampled HN comments                     0.20   discussion attention, not technical/economic validation
```

Os pesos somam 0.70: a cobertura usa esse denominador; a média ponderada bruta usa os pesos presentes. O uso não tem peso no composto. A coorte de referência do percentil é o conjunto exato de famílias de componentes observadas (`gh_trust`, `paper`, `discussion`), não toda a população heterogênea de projetos abertos/fechados. Discussão zero é observada, não ausente. Uma coorte de um único projeto tem percentil de ponto médio 50, o que não prova qualidade mediana. A composição e o tamanho da coorte aparecem em cada card.

```
pct = mid-rank percentile within the available-proxy cohort
Discovery = 50 + coverage * (pct - 50)
```

<a id="usage-metric-families"></a>
### Famílias de métricas de uso

Todo registro de uso reconhecido e com fonte é mantido, inclusive zero observado e valores explicitamente desconhecidos. Não há seleção de “maior número de downloads/usuários”:

| Família | Tipos | O que não estabelece |
|---|---|---|
| `download_operations` | operações de download de npm/PyPI/HF/checkpoint/pacote/app | Usuários únicos, instalações ativas ou clientes; CI/repetições/atualizações podem contar |
| `users` | usuários de extensões, usuários reportados, usuários ativos mensais declarados | Definições de usuário intercambiáveis, clientes pagantes ou resultados econômicos |
| `business_customers` | clientes empresariais | Usuários individuais, downloads ou receita reconhecida |
| `creators` | contagens de criadores | Usuários em geral ou clientes compatíveis |

A normalização exige uma tupla de coorte exata `(family, type, unit, period.start, period.end, scope)`, com todos os elementos observados. Mesmo dentro de uma família, plataformas/tipos, períodos ou escopos diferentes não são agrupados. Metadados de coorte desconhecidos significam `normalized: null`; os valores e as URLs de origem continuam visíveis. Unidades normalizadas ficam presas à coorte nomeada; não são comparáveis entre coortes e nunca entram no composto de descoberta. Independência de origem das fontes, licenças ou datas de período não são inferidas a partir de URLs. Uma lista vazia significa uso não observado, não adoção zero.

<a id="attention-discovery-gap"></a>
## Lacuna entre atenção e descoberta

```
gap = Attention - Discovery
label = attention_ahead   if gap >= +15
        evidence_ahead    if gap <= -15
        similar           otherwise
        insufficient      if gap missing or either coverage < 0.5
```

Isto subtrai posições relativas em **populações de referência de proxies diferentes**, não magnitudes absolutas comparáveis. É uma heurística de descoberta, não “provável hype”, “merecido”, “subestimado”, validade técnica nem valor econômico. Limiares de cobertura não são limiares de precisão. Os cards mostram as observações do analista de pesquisa separadamente; elas não são comprovantes independentes de aceite.

<a id="pulse-topic-map"></a>
## Pulse: mapa de tópicos

A aba Pulse responde "sobre o que é a conversa de IA agora, e onde". Ela é gerada por `pulse.py` (biblioteca padrão) a partir de feeds amostrados e é separada das pontuações de ranking acima.

**Feeds (amostras, nunca totais).** Histórias do Hacker News acima de 20 pontos (Algolia), a tag `ai` do Lobsters, nove hashtags do Mastodon em mastodon.social, dez subreddits de IA por meio do arquivo público do Reddit arctic-shift (um arquivo de terceiros sem garantia de disponibilidade; as contagens de votos lá são retratos de um momento), buscas no Bluesky quando uma senha de app está configurada, doze feeds RSS públicos de newsletters de IA listados em `newsletters.json` (uma rede `Newsletter` separada: o ponto em que um tópico chegou aos resumos (digests); edições de newsletter não criam ligações de menção conjunta e não contam como conversa para o *rising* (em alta)), feeds de anúncios de laboratórios e fornecedores listados em `official_feeds.json` (uma rede `Official` separada: OpenAI, Google DeepMind, Google AI and Research, a sala de imprensa corporativa da Meta, NVIDIA, Microsoft, Mistral, Hugging Face, Qwen, lançamentos do DeepSeek no GitHub e a Anthropic por meio de um espelho RSS comunitário da sua página de notícias, porque ela não publica feed; itens Official são a origem de um lançamento, então podem abrir um rastro de espalhamento, mas nunca contam como conversa, nunca criam ligações de menção conjunta e não somam ao alcance), além dos próprios artigos e repositórios ranqueados do rastreador e do dossiê de pesquisa estático do HYPE. O X não é coletado ao vivo. Cada feed registra `ok`, `partial`, `failed` ou `not connected` na página; um feed com falha mantém os posts que armazenou antes (retenção de 45 dias em `history/signals.sqlite`).

**Tópicos.** Um post é mapeado para tópicos por meio de três regras revisáveis:

1. o léxico em `topics_lexicon.json` (laboratórios, famílias de modelos, produtos, temas, figuras públicas de IA) mais nomes e aliases de projetos do HYPE; nomes de produto curtos e ambíguos só casam diferenciando maiúsculas de minúsculas. As pessoas são figuras públicas citadas em posts (por exemplo Sam Altman, Demis Hassabis, Andrej Karpathy), casadas diferenciando maiúsculas de minúsculas pelo nome completo, e pelo sobrenome apenas quando ele não é ambíguo; um nó de pessoa significa *pessoas mencionadas*, nunca os autores dos posts, e seu `parent` o liga à organização da pessoa quando há uma. Autores de posts nunca são ranqueados;
2. nomes de versão de modelo construídos a partir de famílias versionadas (`Opus 5.5`, `Gemini 4 Argon`, `GPT 6 Astra`): apenas versões de um ou dois dígitos; uma palavra de nível no final (Pro, Flash, ...) ou um codinome com inicial maiúscula passa a fazer parte do nome;
3. frases emergentes: frases de várias palavras com iniciais maiúsculas ou em CamelCase, vindas da conversa ao vivo e ditas por pelo menos três autores distintos, excluindo hashtags, frases feitas só de palavras comuns, frases já cobertas pelas regras 1-2 e uma lista de exclusão no léxico. Elas são desenhadas com contorno tracejado.

Histórias do Hacker News de interesse geral só contam quando usam uma palavra-chave de IA ou citam um modelo, produto ou versão de IA (um alias de laboratório ou de tema sozinho, como "court" ou "Microsoft", não basta). Frases emergentes podem ser nomes de pessoas; pessoas que não são figuras públicas são adicionadas à lista de exclusão quando notadas. Posts do Mastodon e do Bluesky não têm título, então suas amostras mostram até 200 caracteres do texto público do post. O corpo das newsletters é usado apenas para a correspondência de tópicos; a página mostra o título e o link da edição.

**Métricas por janela (24h, 7d, 30d).**

```
voices  = distinct (network, author) pairs among matching posts (for tracker items the author is the lab or repo owner; for newsletters, the newsletter)
weight  = voices × (1 + 0.5 × (networks − 1))          node area grows with √weight
rising  = conversation posts in the last 24h ÷ (conversation posts in 7d ÷ 7)
          live conversation only (HN, Reddit, Mastodon, Lobsters, Bluesky); tracker, dossier and newsletter items are excluded;
          shown only when 7d ≥ 4 and 24h ≥ 2 such posts
spread  = first item per network; a newsletter never takes the earliest slot of a day (many feeds give a date without a time)
edge    = number of posts that match both topics (co-mention); parent links (Opus 5.5 → Claude Opus) are always drawn
```

Votos, visualizações e alcance não entram no peso: não são comparáveis entre redes, e uma única conta viral dominaria. Um nó só é tão forte quanto os posts listados sob ele; o painel lateral os mostra com rede, data e pontuação (o autor de uma rede de conversa nunca é mostrado; veja [Rota do X e dados públicos](#x-route-and-public-data)). A correspondência é lexical, então sarcasmo, negação e citações contam como menções, e um nó de boato registra que as pessoas discutiram um nome, não que a coisa exista.

<a id="briefing"></a>
### Briefing

A aba Pulse abre no **Briefing**: eventos, não tópicos. Um tópico como Claude é discutido todos os dias; um evento como "Meta open-sources Muse Spark" (a Meta abre o código do Muse Spark) acontece uma vez e se espalha. Cada linha do Briefing é um evento dos últimos sete dias.

```
seed      = HN story, Lobsters story, newsletter item or lab/vendor post
join      = same canonical target link, or the same named release (one model version or emerging name per post),
            or idf-weighted title overlap >= 0.45 with two shared uncommon words (each in < 2% of the window's posts)
attach    = a Reddit, Mastodon or Bluesky post joins its release, else the best seed at >= 0.40
chatter   = unmatched posts joined at >= 0.55; one becomes a story only with 5+ voices
carried   = a newsletter whose item names all of the story's key words (up to three uncommon words its editorial posts share)
heat      = (2 x log2(1 + voices) + networks outside newsletters/official + 1.5 x newsletters carrying it
             + 1 if a lab or vendor posted it + log10(1 + HN points)) x 0.5^(hours since the newest post / 48)
```

O título de cada post é lido como uma afirmação, uma pergunta ou uma reclamação (uma queda de serviço, um limite, um bug: uma lista revisável de palavras-chave em `pulse.py`). As manchetes dão preferência a afirmações. Uma história mostra "N% complaints" (N% de reclamações) quando um quarto ou mais dos seus posts são reclamações, e uma história não coberta em que metade dos posts são reclamações é listada em **Complaints** (Reclamações), não como notícia.

Histórias "Covered" (cobertas) têm um post no HN, no Lobsters, em newsletter ou de laboratório, ou são repercutidas por uma newsletter. As demais são listadas como **Chatter, not in the press yet** (burburinho, ainda fora da imprensa): lançamentos que 5+ pessoas discutem no Reddit, no Mastodon ou no Bluesky antes que algum editor os pegue. É aí que a fofoca começa. A manchete é o título editorial mais claro que cita o lançamento (post do laboratório primeiro, depois HN, depois uma história de newsletter), nunca o título de uma edição de resumo (digest). O agrupamento é lexical: um evento descrito em dois vocabulários sem relação entre si pode se dividir em dois, e um nome de lançamento muito comentado reúne tudo o que foi dito sobre ele naquela semana.

<a id="context-panels-jobs-and-page-views"></a>
### Painéis de contexto: Empregos e visualizações de página

O painel de Empregos diz "nenhuma fonte qualificada" para qualquer mudança em empregos atribuída à IA: nenhuma fonte que examinamos mede isso (BLS, O*NET, Indeed Hiring Lab, Challenger e Layoffs.fyi foram conferidas quando o briefing foi projetado). Abaixo dele o briefing mostra **contexto, não previsão**, de duas fontes gratuitas lidas sem chave uma vez por execução ao vivo (`indicators.py`; as séries, os termos e os tópicos ficam fixos em `indicators.json`):

| Fonte | O que mostramos | Termos (lidos em 2026-10-18) | Limites |
|---|---|---|---|
| [API pública v1 do BLS](https://www.bls.gov/developers/api_faqs.htm) | seis séries nacionais com ajuste sazonal: o total de empregos não agrícolas e a taxa de desemprego como referência, e os empregos em editoras de software, em projeto de sistemas de computação, em infraestrutura de computação e hospedagem de dados, e em serviços de apoio a empresas (centrais de atendimento), os setores cujo trabalho é do tipo que ferramentas de IA hoje fazem ou ajudam a fazer; para cada uma, o mês mais recente (marcado quando preliminar) e o mesmo mês um ano antes, como o BLS os publica | [domínio público](https://www.bls.gov/opub/copyright-information.htm); os [termos da API](https://www.bls.gov/developers/termsOfService.htm) pedem a data de obtenção e a declaração "BLS.gov cannot vouch for the data or analyses derived from these data after the data have been retrieved from BLS.gov." (o BLS.gov não pode garantir os dados nem as análises derivadas deles depois que os dados foram obtidos do BLS.gov), as duas mostradas com o painel | dados gerais do mercado de trabalho: nenhuma série atribui uma mudança à IA; 25 consultas por dia sem chave, e fazemos uma |
| Hacker News "Who is hiring?" (Algolia) | para os dois tópicos mensais mais novos, os posts de primeiro nível e os que citam no texto um termo de IA de `indicators.json` (AI, ML, LLM, machine learning e alguns outros) | a Y Combinator publica os dados pela sua [API pública](https://github.com/HackerNews/API) e não declara licença; os seus [termos de uso](https://www.ycombinator.com/legal/) proíbem raspar o próprio site; só contagens: nenhum texto de post nem nome de quem postou é guardado | uma menção em qualquer parte do post (inclusive a empresa se descrevendo), não uma contagem de vagas de IA; um mês ainda aberto conta os posts até agora |

**Visualizações de página na Wikipédia (artigos de IA)** é atenção a uma lista fixa de artigos sobre a IA como assunto (sete na Wikipédia em inglês e sete na Wikipédia em português, nenhuma página de empresa ou produto), não consciência: visualizações de usuários (robôs de busca e agentes automáticos excluídos) somadas nos 7 dias que terminam no dia mais novo que a [API de pageviews da Wikimedia](https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/documentation/access-policy.html) devolve (dados sob CC0 1.0, termos lidos em 2026-10-18), ao lado dos 7 dias anteriores. Os dois totais aparecem; não há razão nem seta. O total de um projeto é nulo a menos que todo artigo da lista tenha devolvido os 14 dias.

Toda leitura de contexto é uma prévia com sua cobertura, sua data de obtenção e os termos sob os quais foi lida. As três fontes rodam em paralelo entre si e junto com os coletores dos feeds, sob um orçamento único de 45 segundos: nenhuma requisição começa depois que o orçamento acaba, cada leitura de rede expira após o tempo restante (no máximo 15 segundos) e nada é tentado de novo, então a etapa termina em cerca de 60 segundos no pior caso e pouco acrescenta à execução; uma fonte que falha fica nula com o motivo, nunca 0, e nenhum valor vem de uma execução anterior. A entrada guardada é `history/indicators.json` (para o Hacker News, só ids, títulos e contagens dos tópicos); ela vai inteira para o manifesto de entrada do dia quando é desta execução (senão o manifesto diz null), então um recálculo não precisa de nenhuma chamada.

<a id="hub-check-models-on-the-hugging-face-hub"></a>
### Verificação no Hub: modelos no Hugging Face Hub

Uma história com nome de lançamento (uma versão de modelo como "Qwen 3.8", ou um nome emergente como "Muse Spark") é buscada uma vez por execução ao vivo no [Hugging Face Hub](https://huggingface.co/docs/hub/api) (`hub.py`): os 100 modelos cujo id corresponde ao nome, primeiro os mais baixados nos últimos 30 dias. Um modelo conta quando sua organização está em `hub_orgs.json`, uma lista revisada pelo responsável de laboratórios e empresas que publicam os próprios modelos (nunca a conta de uma pessoa), e seu nome traz as palavras e os números do nome de lançamento na ordem, a versão exata ("Qwen 3" não é Qwen3.8, "Gemma 2" não é gemma-2b). O registro mostra quantos desses modelos estão entre esses 100 resultados e os cinco mais baixados, cada um com a data de criação, os downloads nos últimos 30 dias (o número do próprio Hub) e as curtidas. Em Hype vs substância, uma história com um ou mais desses modelos tem substância registrada.

A leitura é estreita de propósito. 0 modelos quer dizer nenhum sob uma organização listada entre esses 100 resultados: o modelo pode ser fechado, publicado com outro nome ou por outra conta, ou ainda não ter saído, e um nome de lançamento que nem é um modelo (uma expressão emergente como uma empresa ou um cargo) também dá 0. Um modelo sob uma organização listada não prova que quem o criou o lançou (a NVIDIA, por exemplo, publica cópias quantizadas de modelos de outros laboratórios), e um nome de lançamento muito buscado pode tirar os modelos de quem o criou dos 100. Uma história sem nome de lançamento diz "sem nome de lançamento"; uma busca que não rodou ou falhou diz "não buscado", nunca 0. Há uma requisição por nome, uma depois da outra, primeiro a história mais quente, sob um orçamento de 40 segundos (um nome que o orçamento não alcança diz "não buscado"), e nada é tentado de novo; um nome sem letra latina nem dígito não é buscado. Nenhuma chave é necessária (um `HF_TOKEN`, quando definido, só aumenta o limite de requisições). A entrada armazenada é `history/hub.json`: por nome, só o id, a data de criação, os downloads e as curtidas dos modelos das organizações listadas; ela vai inteira para o manifesto de entrada do dia quando é desta execução (senão null). [Termos de serviço](https://huggingface.co/terms-of-service) do Hub lidos em 2026-10-18; publicamos ids e contagens de modelos, nunca cards ou arquivos de modelos.

<a id="data-identity-stable-ids"></a>
### Identidade dos dados (ids estáveis)

Todo registro mantém um id que é função pura da sua fonte, de modo que os dados podem ser migrados para outro banco (como um grafo de conhecimento) a qualquer momento e reimportados sem duplicatas.

```
post   = (network, pid): HN objectID, Reddit/Mastodon/Lobsters/Bluesky post id, feed item link for newsletters and labs
topic  = lexicon id (topics_lexicon.json), "v:" version slug, or "e:" + slug of an emerging phrase
story  = "s:" + first 12 hex of sha1("release:" + topic id for a story about one named release,
         else the canonical target link of its earliest editorial post, else that post's URL)
repo   = owner/name    paper = arXiv id
```

Cada história, amostra de tópico e passo de espalhamento mostrado carrega a URL do post original; um post só de contagem não carrega nenhuma.

<a id="what-s-new"></a>
### O que há de novo

A aba Pulse abre em **What's new this week** (novidades da semana): tópicos que mudaram, não tópicos que são sempre grandes. Claude, OpenAI ou "AI agents" são discutidos todos os dias; uma lista ordenada por tamanho não diz nada a quem lê diariamente. Cada tópico recebe duas pontuações e é ranqueado pela maior delas.

```
talk   = this week's share of posts / share in days 8-30, on the deep networks only, baseline smoothed by +1 post
         deep network = live network with posts on >= 70% of the baseline days and >= 50 baseline posts
         qualifies with >= 2 deep-network posts this week, >= 5 voices and >= 2 networks in the last 7 days
build  = tracker repos matching the topic that were born in the last 30 days
         (a repo in a tracker paradigm, such as JEV, counts only for that paradigm's theme)
         qualifies with >= 3 born repos that are at least half of the topic's repos (a new wave, not an old field)
rank   = max(percentile of log(talk) among qualifying topics, percentile of build among qualifying topics)
always-on = mentioned on the deep networks on >= 60% of the baseline days with talk < 2: its talk score does not count
```

Proporções, não contagens, porque o volume de coleta muda: o banco começou em datas diferentes para cada rede. Em outubro de 2026, só o Hacker News e as newsletters têm histórico longo o bastante para serem profundas; o Reddit (cerca de uma semana de arquivo) e o Mastodon (esparso antes de meados de outubro) entram automaticamente quando o histórico armazenado deles atender à regra. Um aumento é relativo ao que amostramos, não à internet inteira, e dois posts contra nenhum é um número pequeno: cada cartão mostra as contagens por trás dele. Um cartão também mostra a manchete mais recente, a primeira aparição em cada rede (o caminho de espalhamento) e as pessoas e os assuntos citados junto com o tópico.

<a id="signal-what-matters-now"></a>
### Sinal: o que importa agora

A lista "Biggest right now" (os maiores agora; antes "What matters now") ordena os tópicos por um **sinal** por janela, de 0 a 100. É uma heurística para ordenar a atenção nos feeds que amostramos, não uma medida de verdade, qualidade ou importância.

```
signal      = 0.40 × pct(voices) + 0.25 × pct(reach) + 0.20 × pct(rising) + 0.15 × pct(engagement excl. Reddit)
pct(x)      = share of the other topics on the map (up to 160, all kinds) with a strictly lower value; ties share the lower rank; a zero value scores 0
reach       = distinct networks other than newsletters and Official (tracker arXiv/GitHub and dossier platforms count as networks, as in `nets`)
              + distinct newsletters carrying the topic in the window
rising      = the node's 24h-vs-7d ratio above (one value for every window); a topic without a rising value, or with a ratio below 1
              (slower today than its 7-day average), scores 0 on this component
engagement  = Σ log(1 + score + comments) over matching posts outside Reddit (arctic-shift Reddit scores are snapshots taken at ingestion)
```

Um tópico sem vozes na janela recebe 0. As vozes nunca incluem feeds oficiais (Official): um fornecedor anunciando o próprio produto é a origem, não uma voz. Os quatro percentis são armazenados junto com o sinal (`signal_parts`) e a página sempre mostra as contagens por trás deles (vozes, redes, newsletters, em alta) em vez do número puro. **A cor no mapa é o alcance** (uma única escala de azul em cinco faixas fixas: 1, 2, 3–4, 5–7, 8+; nós que alcançam 5 ou mais também brilham), o tamanho continua sendo as vozes, e a forma é o tipo de tópico (círculo para modelo, quadrado para laboratório ou produto, losango para pessoa, hexágono para tema, contorno tracejado para emergente). Cada nó também registra quais newsletters o trouxeram e as somas brutas de pontuação e de comentários por rede nos seus posts ao vivo amostrados (`engagement`; pontos no HN, favoritos + boosts no Mastodon, votos do snapshot no Reddit); são somas sobre a nossa amostra, nunca totais da plataforma.

<a id="who-and-where"></a>
### Quem e onde

Cada tópico registra, por janela, os posts e as vozes distintas por rede (`where`), as newsletters que o trouxeram e as pessoas (`kind: person`) e os assuntos mais citados nos mesmos posts (`with`, a partir das contagens de menção conjunta; itens de newsletter e oficiais não geram menções conjuntas). A aba Pulse os mostra como mapa (Map) ou como tabela ordenável (Table); a tabela e o painel lateral nunca ranqueiam autores de posts.

<a id="reach-percentile-across-papers-posts-and-repos"></a>
### Percentil de alcance entre artigos, posts e repositórios

```
reach_pct = mean of the five highest item percentiles among the items that match the topic in the window
item percentile = share of the other items of the same type and window with a strictly lower value (ties share the lower rank; zero scores 0)
types     = posts, ranked per network: HN points, Mastodon favourites + boosts, Lobsters score, Bluesky likes + reposts
            papers: Hugging Face upvotes of tracker papers
            repos: stars gained in the window (tracker rows, any paradigm view)
```

O Reddit fica de fora porque as pontuações do arctic-shift são snapshots tirados na ingestão; itens de newsletter e oficiais não têm pontuação. Contagens brutas nunca são somadas entre tipos: um tópico fica perto do topo quando seus poucos melhores itens estão perto do topo do próprio tipo. Um tema com `tracker_tag` no léxico (JEV) também herda todos os repositórios do rastreador daquele paradigma, casados ou não, tanto para este percentil quanto para o sinal de coordenação de repositórios. Itens sem valor observado ficam de fora, então um tópico sem nenhum item pontuado não tem percentil de alcance (mostrado como —). Isso é separado da cor no mapa (`reach` = redes + newsletters).

<a id="organic-or-orchestrated"></a>
### Orgânico ou orquestrado?

Seis sinais por tópico sobre a conversa ao vivo de 30 dias (HN, Reddit, Mastodon, Lobsters, Bluesky) feita por contas com nome (autores vazios, `[deleted]` e `AutoModerator` ficam de fora). Eles descrevem padrões que campanhas coordenadas deixam; cada um também tem causas inocentes, então a página os apresenta como sinais, nunca como prova.

| Sinal | Definição | Dispara em | Explicação inocente |
|---|---|---|---|
| burst | proporção de posts dentro da janela de 6 horas mais densa | ≥ 0.5 (forte ≥ 0.7) | um dia de lançamento ou de notícia |
| dupe | proporção de posts com 5+ palavras cujo Jaccard de shingles de 5 palavras (em minúsculas, sem URLs) com um post de um autor **diferente** é ≥ 0.6; posts com menos de 5 palavras ficam fora do numerador e do denominador; exige 10 posts comparáveis | ≥ 0.2 (forte ≥ 0.4) | muitas pessoas enviando o mesmo título de matéria |
| single_topic | entre os autores do tópico com **dois ou mais** posts ao vivo armazenados em 30 dias (todos os posts contam, inclusive histórias do HN descartadas depois por não serem de IA), a proporção cujos posts casam todos com este tópico; autores de um só post não podem ser distinguidos de quem posta de passagem e não são contados; exige 5 desses autores | ≥ 0.5 | especialistas que só postam sobre um projeto |
| link_push | maior proporção de posts apontando para uma mesma URL de destino (sem fragmento e sem parâmetros utm/ref); exige 10 posts com link conhecido. Os links de destino são guardados a partir de 2026-10-16, então posts mais antigos são desconhecidos, não zero | ≥ 0.3 com 5+ posts (forte ≥ 0.5) | um anúncio oficial que todo mundo linka |
| repos | repositórios do rastreador ranqueados na janela de 30 dias que casam com o tópico (por texto, ou por paradigma no caso de um tema com `tracker_tag`), com suas flags antirruído (`stars>activity`, `solo`, `spike`); a proporção de `stars>activity` em todas as linhas de 30 dias é mostrada como linha de base | `stars>activity` em metade de 3+ repositórios | repositórios jovens cuja atividade ainda não acompanhou |
| dossier | a avaliação de coordenação do dossiê de pesquisa HYPE para os projetos mapeados para o tópico | patrocínio declarado ou uma avaliação de coordenação medida | — |

`link_push` que não pode ser medido aparece como *unknown / not measured* (desconhecido / não medido), o que é diferente de um sinal que foi medido e não disparou. A janela de 30 dias só é tão profunda quanto a coleta: o Reddit (cujo arquivo também alcança cerca de uma semana para trás a cada execução) e o Mastodon começaram há pouco, então, nas primeiras semanas de coleta, a janela deles é mais rasa que 30 dias. O X não é coletado ao vivo, então campanhas feitas lá são invisíveis aqui; toda leitura diz respeito à nossa amostra.

Rótulo: **too few posts** (poucos posts) abaixo de 10 posts; **strong coordination signals** (sinais fortes de coordenação) quando dois sinais disparam ou um atinge seu nível forte; **some coordination signals** (alguns sinais de coordenação) quando um dispara; caso contrário, **no coordination signal** (nenhum sinal de coordenação). Os limiares são deliberadamente conservadores e não validados; um rótulo é um motivo para ler os posts, não uma conclusão.

<a id="newsletter-citations"></a>
### Citações em newsletters

Quando um item de newsletter é processado, os links do seu HTML são lidos antes de o HTML ser descartado: os domínios citados e os handles do X/Twitter (`x.com/<handle>/…`) são armazenados com o item. O campo `citations` de `pulse.json` lista, por janela, os 50 domínios mais citados, com o número de itens que os citam e quais newsletters os citaram. A infraestrutura de newsletters (Substack, beehiiv, t.co, serviços de rastreamento) e o próprio site da newsletter e seus subdomínios (`site` em `newsletters.json`) são ignorados; links de patrocinadores não são, então anunciantes podem aparecer. Os handles do X citados **não são publicados**: uma lista ranqueada de contas (muitas vezes pseudônimas) não cabe no site público. Eles são gravados em `history/citations.json` (com contagens, newsletters e tópicos) como uma lista privada de candidatos a seguir para o dono do projeto (veja `docs/SIGNALS_PLAN.md`).

<a id="live-column-on-the-hype-tab"></a>
### Coluna ao vivo na aba Hype

`pulse.json` traz `projects`: para cada id de projeto HYPE, as vozes, os posts e as redes em 7 e em 30 dias entre os posts **ao vivo** amostrados (HN, Reddit, Mastodon, Lobsters, newsletters; nunca o rastreador nem o dossiê de pesquisa estático) que casam com o nome ou os aliases do projeto; feeds oficiais de fornecedores nunca contam. Um valor 0 significa nenhum post correspondente nos nossos feeds amostrados, não atenção zero; um traço significa que o arquivo do Pulse está indisponível. As colunas do dossiê de pesquisa na aba Hype continuam sendo uma amostra estática na data de corte de conteúdo do dossiê.

<a id="timestamp-proof"></a>
## Prova de carimbo de tempo

O manifesto de entrada de cada dia (o arquivo na sua Release datada do GitHub, cujo SHA256 o registro anota) recebe uma prova [OpenTimestamps](https://opentimestamps.org), `web/ledger/ots/YYYY-MM-DD.ots`, feita pelo cliente JavaScript `opentimestamps` fixado exatamente na 0.4.9 (LGPL-3.0, instalado sem modificação a partir de `scripts/checks/package-lock.json`). A atualização envia só o SHA256 do manifesto aos calendários públicos do OpenTimestamps, então a prova é registrada **pendente**: os calendários se comprometem a colocá-la em uma transação de Bitcoin. Cada atualização seguinte roda o `upgrade` do cliente em toda prova que nenhuma entrada do registro anota como ancorada, registra o arquivo atualizado no mesmo lugar e confere cada prova completa com `verify --ignore-bitcoin-node`. A data e a altura do bloco de Bitcoin de cada prova aceita vão para a entrada **da própria execução** (`anchored`); entradas anteriores nunca são editadas, e uma prova nunca muda depois que uma entrada do registro anota o seu bloco. A página de auditoria só mostra "ancorada" para uma data quando uma entrada do registro anota o seu bloco; antes disso, "pendente". A entrada do próprio dia guarda `ots.sha256`, o SHA256 da prova **no momento do carimbo** (o arquivo pendente como foi publicado pela primeira vez); depois o arquivo muda no lugar quando é atualizado, então o seu SHA256 atual é o `ots_sha256` do registro posterior que o ancora, e a partir daí ele nunca muda.

**Em que a atualização confia.** A atualização não roda um nó de Bitcoin. `verify --ignore-bitcoin-node` pega o cabeçalho do bloco no explorador público Esplora em `https://blockstream.info/api` e **assume que o bloco desse explorador é válido**; um explorador errado poderia fazer uma prova falsa parecer ancorada. Quem tem um nó de Bitcoin pode dispensar essa confiança: baixe o manifesto da sua Release e a prova do site e rode `ots verify`, que confere o cabeçalho no próprio nó (o primeiro comando abaixo; o segundo é a rota da atualização pelo explorador). Uma prova diz só que o manifesto existia até o horário daquele bloco; ela não diz que algum veredito está certo.

```
ots verify -f manifest-YYYY-MM-DD.json.gz YYYY-MM-DD.ots
npx -p opentimestamps@0.4.9 ots-cli.js verify --ignore-bitcoin-node -f manifest-YYYY-MM-DD.json.gz YYYY-MM-DD.ots
```

<a id="known-biases"></a>
## Vieses conhecidos

- **Dominância do HN**: as menções em Papers e a maioria dos posts do HYPE vêm do Hacker News, que sobrerrepresenta ferramentas para desenvolvedores e sub-representa trabalhos puramente de pesquisa e os que não estão em inglês.
- **Seleção do HF**: só artigos publicados no HF têm upvotes; a falta de upvotes conta como dado ausente, não como pesquisa fraca.
- **Busca de candidatos**: a correspondência por palavra-chave/tópico, a indexação das fontes e o filtro pela janela de criação/push excluem trabalhos relevantes com vocabulário, idiomas ou padrões de atividade diferentes. São coortes descobertas por seleção intencional, não populações representativas.
- **Seleção do enriquecimento**: as coletas de atividade limitadas por cota favorecem repositórios ordenados como promissores; os 100 alvos de enriquecimento autenticados ou 30 não autenticados não são amostras aleatórias. Cobertura e encolhimento não conseguem remover esse viés de seleção. As contagens de consultas e as populações de referência alteram os rankings; disso não decorre nenhuma afirmação de acurácia não validada.
- **Histórico jovem**: os deltas entre snapshots cobrem o intervalo entre nossas execuções, não a janela inteira, até que se acumulem execuções suficientes. Proxies de taxa favorecem artigos e repositórios que atingiram o pico cedo.
- **O encolhimento em direção ao prior de referência** pode rebaixar no ranking trabalhos genuinamente fortes, mas pouco observados. Projetos fechados e abertos não são igualmente observáveis; não interprete a ausência de dados como capacidade fraca ou baixo valor de negócio.
- **Amostra de pesquisa (HYPE)**: intencional e só com dados públicos. Contagens de seguidores, datas de pico e as verdadeiras origens virais são, em sua maioria, desconhecidas e aparecem como —.

<a id="versioning"></a>
## Versionamento

- A versão atual é `3.0` no código/config; a semântica da fórmula e das coortes mudou, por isso a versão principal (major) é incrementada. Mudanças menores (minor) ajustam pesos/limiares sem alterar as medições.
- `score_run(features, version='2.0')` usa a configuração `legacy_v2` completa e congelada, não os parâmetros atuais mutáveis. `legacy_v2_real_scores` e `legacy_v2_hype_window` preservam a aritmética e os rótulos históricos apenas para avaliação explícita. A V2 era um método de descoberta: seus rótulos “Real”, “trust”, “confidence” e de uso agregado não estabeleciam capacidade, veracidade nem uma magnitude de adoção comparável.
- `score_run(features, version='1.0')` continua sendo avaliação histórica. Versões não suportadas falham em vez de rodar silenciosamente as fórmulas atuais.
- `web/data.json` é explicitamente um **artefato numérico arquivado da v2.0**. Seu manifesto completo de entradas e as interseções de PRs criados e mesclados não estão disponíveis aqui. Pontuações, valores brutos, prior, horários originais de geração e `config_sha` permanecem inalterados; a cobertura renomeada e as dimensões desconhecidas separadas esclarecem o significado. A antiga razão de PRs é rotulada como histórica, enquanto a razão da coorte atual está ausente. Nada aqui implica uma repontuação v3 fabricada nem um comprovante de disponibilização/deploy.
- `web/hype.json` é uma projeção offline, no método 3.0, de observações publicadas preservadas. Seu proxy upstream do GitHub, quando presente, é atividade histórica da v2, identificada explicitamente; nenhuma coorte corrigida, atualidade nova das fontes ou aprovação de fonte é inventada.
- Execuções completas normais retêm snapshots de features. `python3 run.py --rescore` exige as entradas reais de cache/histórico; as visões de publicação não conseguem recriar um manifesto de features completo e imutável.
- A página lê `web/METHODOLOGY.md`; mantenha-o idêntico a este arquivo. Não há hoje nenhum workflow de CI upstream que comprove essa igualdade.

<a id="how-to-propose-changes"></a>
## Como propor mudanças

1. Edite `scoring_config.json` (pesos, limiares) ou `scoring.py` (fórmulas) e atualize este arquivo no mesmo PR.
2. Rode `python3 -m unittest discover tests` e `python3 eval.py --features tests/fixtures/features_a.json tests/fixtures/features_b.json --hype tests/fixtures/hype_small.json --compare-v2`.
3. Relate a estabilidade, a completude das coortes, a ausência de dados antes/depois e os rótulos descritivos alterados; nada disso valida a acurácia.
4. Explique a correção de medição, a coorte compatível e a política para dados ausentes. “Meu projeto favorito sobe” não é motivo.

Veja [CONTRIBUTING.md](CONTRIBUTING.md) para fontes de dados, listas de sementes e a regra de nunca inventar números.

<a id="licence"></a>
## Licença

A partir do commit que adiciona esta seção e substitui o arquivo `LICENSE` MIT (`git log --follow -- LICENSE` mostra qual é), o dehype tem estas licenças:

- **Código** (tudo neste repositório que não é dado): [AGPL-3.0](LICENSE), a GNU Affero General Public License, versão 3 ou (a seu critério) qualquer versão posterior. Quem roda uma cópia modificada como serviço de rede oferece aos usuários o código-fonte dessa versão.
- **Dados** (`web/*.json`, os quatro feeds, `web/ledger/` e os arquivos das Releases datadas): [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), cobrindo apenas a nossa seleção, organização e campos calculados: pontuações, contagens, cobertura, ids de histórias, valores dos medidores, estados de evidência e o nosso próprio texto. Ela não relicencia o que não fizemos: títulos de posts, manchetes, nomes, links e outros textos de terceiros mantêm os termos de seus donos, e cada fonte mantém os seus (os metadados do arXiv são CC0).
- **Versões anteriores mantêm sua licença.** Todo commit e release anterior a esse commit, incluindo a versão 2.0 de 2026-10-07, continua disponível sob MIT para o código e CC BY 4.0 para os dados; esta mudança não revoga nenhuma das duas concessões.
- Código de terceiros mantém sua própria licença e aviso: Cordis (MIT) em `scripts/dehype/NOTICE`, e o cliente OpenTimestamps (LGPL-3.0) em `scripts/checks/NOTICE`; a busca por sentido carrega o transformers.js (Apache-2.0) e o onnxruntime-web (MIT) dos próprios pacotes.

<a id="issue-11-change-record-and-attributed-rulings"></a>
## Registro de mudanças da issue 11 e decisões atribuídas

Antes do reparo, o código real da v2 selecionava um milhão de operações de download em detrimento de cem clientes empresariais e normalizava downloads/usuários/clientes nas unidades 1.000/0.500/0.334. O `run.build_features` real emitia merge 2.0 para dez eventos de abertura/vinte de merge, apesar de uma interseção conhecida de quatro membros, e 0.0 para um denominador de PRs vazio. O código atual mantém registros de fonte separados, não normaliza coortes desconhecidas, usa a fração da interseção e mantém como ausentes as coortes vazias/desconhecidas. As fixtures de limite são explicitamente sintéticas; as fixtures de features/HYPE versionadas no repositório são subconjuntos preservados, não uma verdade de referência (ground truth) de acurácia.

Comparação observada da fixture HYPE versionada (`hype_small.json`, SHA256 `4eb7b06dcffaf937d88150254e031e19e378f702b910b2d403a54bf77bc72e7f`):

| Projeto | Pontuação histórica v2 | Descoberta atual | Tratamento atual do uso |
|---|---|---|---|
| Claude Code | 72.0 | 60.5 | 52,946,380 operações npm retidas; coorte de período/escopo desconhecida, valor normalizado ausente; excluído do composto |
| Higgsfield | 61.2 | 48.5 | 32,000,000 usuários informados retidos como alegação do fornecedor; coorte compatível desconhecida; excluído do composto |
| Gemini app | 59.6 | 62.0 | O uso continua não observado; a pontuação é apenas descoberta por discussão, não uma constatação sobre clientes/capacidade |
| Reflection Beam | 40.4 | 37.2 | O uso continua não observado; o zero observado de discussão amostrada continua sendo zero |

As pontuações mudam porque o uso é excluído, o denominador da cobertura passa a ser 0.70 e os percentis usam coortes de proxies disponíveis. São efeitos explicados do método, não evidência de que os rankings ficaram mais precisos. `eval.py --compare-v2` imprime todas as linhas da fixture; a estabilidade temporal do HYPE continua sem medição. As fixtures de features da execução completa não têm interseções de PR, então a cobertura atual de repositórios exclui o sinal de merge delas, enquanto a reexecução explícita da v2 preserva os resultados históricos.


- **Decisão — issue-11-engineer:** Incrementar para o método 3.0 e congelar os parâmetros executáveis completos da v2 — preserva uma reexecução histórica honesta da descoberta sem rerrotular saídas antigas — custo se estiver errado: o código/config histórico continua sendo mantido para avaliação explícita.
- **Decisão — issue-11-engineer:** Excluir o uso do composto e reter cada métrica de fonte reconhecida com os metadados exatos da coorte — operações/usuários/clientes não têm uma magnitude comum — custo se estiver errado: menos sinais de ranking no composto e registros não normalizados quando faltam metadados.
- **Decisão — issue-11-engineer:** Usar coortes de proxies disponíveis e rótulos descritivos de atenção/descoberta — discussão/upvotes/atividade não conseguem estabelecer capacidade nem validade de negócio — custo se estiver errado: coortes pequenas oferecem resolução de ranking limitada.
- **Decisão — issue-11-engineer:** Expor a completude ponderada como cobertura, com verificação/atualidade/independência não qualificadas — contagens não podem fabricar qualificação de proveniência — custo se estiver errado: os consumidores precisam inspecionar dimensões separadas.
- **Decisão — issue-11-engineer:** Medir o subconjunto mesclado da coorte de PRs criados; omitir coortes não observadas/vazias/inválidas em vez de truncar eventos — corrige denominadores incompatíveis — custo se estiver errado: uma consulta pública adicional ao Search por repositório enriquecido e menos cobertura histórica.
- **Decisão — issue-11-engineer:** Preservar `web/data.json` como arquivo numérico da v2 em vez de reconstruir entradas ausentes; o coordenador aceitou explicitamente esse encaminhamento — a identidade honesta do artefato vale mais que pontuações atuais falsas — custo se estiver errado: uma projeção atual, corrigida e completa do GitHub aguarda as entradas reais de uma execução completa, não contagens de interseção inventadas.
- **Decisão — issue-11-engineer:** Mover a criação de diretórios em tempo de execução para `main`, deixando os imports sem efeitos colaterais para as fixtures de extração em memória — os limites reais de consulta/feature podem ser exercitados sem mutação de cache/histórico — custo se estiver errado: consumidores que dependiam de diretórios criados no import precisam usar o ponto de entrada de runtime existente.
- **Decisão — issue-11-engineer:** Totais parciais/ausentes do Search permanecem não observados, e caches legados recentes sem interseção de coorte são requalificados — caso contrário, uma resposta incompleta pode inventar atividade zero — custo se estiver errado: leituras permitidas adicionais na próxima execução autorizada do coletor, nunca leituras durante esta qualificação offline.
- **Decisão — issue-11-engineer:** Exibir a cobertura com duas casas decimais na avaliação e usar um cabeçalho de Methodology neutro quanto à versão — evita arredondar 0.75 para 0.8 ou apresentar a documentação atual como o método arquivado — custo se estiver errado: tabelas de avaliação um pouco mais largas.

<a id="implementation-qualification-receipt"></a>
### Comprovante de qualificação da implementação

O worker de implementação executou estes comandos locais sobre a fatia concluída de código-fonte/config, após reparos delimitados de fechamento das fixtures e de precisão de exibição:

| Evidência | Resultado observado |
|---|---|
| `python3 -m unittest discover -s tests -p test_scoring.py` | Saída 0; 26 testes; zero falhas, erros ou avisos |
| `python3 eval.py --issue11-smoke --features tests/fixtures/features_a.json tests/fixtures/features_b.json --hype tests/fixtures/hype_small.json --compare-v2` | Saída 0; verificações diretas de família/ausência de dados/PR/dimensionais, mais todas as 25 linhas de fixture antes/depois |
| `python3 -m unittest discover tests && python3 eval.py --features tests/fixtures/features_a.json tests/fixtures/features_b.json --hype tests/fixtures/hype_small.json` | Saída 0; 43 testes e avaliação completa; zero falhas, erros ou avisos |
| Regressão permanente de extração de PR contra o `run.py` original capturado | Falha na asserção pretendida: `2.0 != 0.4`; passa na suíte atual focada/completa |
| Execução explícita da v2 contra o `scoring.py` original capturado e a config original | Igualdade exata nas duas fixtures de features completas, nas tuplas de trust e nos campos históricos do HYPE em overall/30d/7d |
| Preservação do artefato numérico histórico | Todas as 7,706 linhas de visualização de artigos/repositórios preservam as pontuações numéricas, os valores brutos e a posição/movimento originais; método/config/prior/horários de geração inalterados |
| Navegador real em 1280px e 390px | As linhas/cards atuais do HYPE mostram as unidades das fontes, o uso não observado, as coortes de período/escopo ausentes e as dimensões não qualificadas separadas; GitHub arquivado e Methodology renderizada inspecionados; nenhum erro de JavaScript observado |

`PYTHONDONTWRITEBYTECODE=1` estava definido no ambiente para os gates de Python, não era um comando substituto. As fixtures iniciais de SQLite com gerenciador de contexto passavam, mas emitiam ResourceWarnings; fechar a conexão explicitamente eliminou o vazamento antes da qualificação final. A regressão original de PR foi exercitada com uma fixture sintética de resposta da API pública, sensível a datas, no limite real de Search/extração, e não por inspeção da query string no código-fonte nem por uma alegação de coleta ao vivo.

As capturas de tela do navegador foram feitas com a ferramenta Chromium gerenciada já existente, depois que o comando de screenshot do Orca retornou uma imagem 1×1 inutilizável; essa imagem não foi tratada como prova visual. Em 390px, a tabela/card larga existente exige rolagem horizontal; as unidades/dimensões do lado direito foram inspecionadas depois da rolagem. Não se afirma nenhum redesenho responsivo, auditoria de acessibilidade, verificação de fontes, acurácia de capacidade, coleta ao vivo, aprovação editorial nem deploy. As entradas imutáveis completas para uma repontuação atual e corrigida do GitHub continuam indisponíveis sob o encaminhamento de arquivo histórico explicitamente aceito.

A revisão independente de aceite/design e a revisão de qualidade separada são gates do coordenador, não o veredito deste implementador. A evidência local não estabelece aceite em produção nem autoriza o fechamento da issue. Nenhum novo caminho de repositório, chamada paga/de modelo, aquisição de fontes, reinício de serviço compartilhado, mutação de estado do Git, commit, mutação na forja nem deploy foi realizado por este worker.

