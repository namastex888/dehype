# Política do dehype: vereditos, direito de resposta, correções e remoções

English: [POLICY.md](POLICY.md). Esta página é publicada antes do primeiro veredito FALSE e é verificada em cada build.

## Vereditos

O dehype rotula alegações, histórias, temas e projetos, nunca pessoas ou contas. Há cinco rótulos:

- **REAL**: uma fonte primária confirma a alegação nomeada.
- **OVERHYPED**: uma fonte primária mostra que a alegação é verdadeira só em parte, ou menor do que foi apresentada.
- **FALSE**: uma fonte primária citada contradiz a alegação nomeada.
- **PUSHED**: um documento público (um registro oficial, uma marcação de patrocínio, uma admissão) mostra uma ligação paga ou material não declarada por trás da história.
- **UNVERIFIED**: ainda não conferido com uma fonte primária.

Toda história começa como "proposta pelo pipeline, não revisada". O pipeline escreve um registro de evidência com o estado "proposed" e nenhuma palavra de rótulo; ele nunca propõe um rótulo. Só o responsável muda um rótulo, por um pull request em `web/verdicts.json`, e o merge é a confirmação. A atualização diária nunca escreve esse arquivo: ela prepara uma lista fixa de arquivos escritos pelo robô que o deixa de fora e, antes de enviar seu commit, roda a verificação dos arquivos do responsável (`scripts/check_owner_files.py`), de modo que um commit da atualização que o tenha alterado nunca é enviado. A CI e o deploy rodam a mesma verificação em toda outra mudança. Há uma linha por alegação: duas linhas sobre a mesma história com a mesma alegação ou o mesmo documento são rejeitadas, e um veredito alterado altera a sua linha.

Uma linha com rótulo REAL, OVERHYPED, FALSE ou PUSHED traz:

- a alegação nomeada (para PUSHED, o documento);
- a URL de uma fonte primária, que nunca é um post do X, do LinkedIn ou do YouTube. Uma alegação cuja única fonte é um post do X fica UNVERIFIED; o motivo pode nomear a conta oficial e a data, sem link;
- um motivo em inglês e em português;
- o commit de confirmação e a data em que foi confirmada. O commit de confirmação é o que atribui o rótulo; um commit não pode citar a si mesmo, então a linha o cita num commit seguinte do mesmo pull request.

FALSE só é atribuído pelo responsável, à mão, a uma alegação nomeada, com uma fonte primária citada que a contradiz. PUSHED exige o documento público citado na linha; sinais de coordenação aparecem como "sinais de coordenação" e nunca como rótulo. Toda linha FALSE aponta para o direito de resposta e as correções abaixo (`POLICY.md#reply`).

Uma linha nomeia uma história pelo seu id (`s:` e 12 hexadecimais). O id de uma história pode mudar quando chega um post mais antigo; a atualização registra então a mudança em `web/story-aliases.json` (id antigo para id novo), e a linha a acompanha. Os ids publicados em cada dia passam a ficar num arquivo de ids (`web/ledger/ids/AAAA-MM-DD.json`, escrito quando o registro diário estiver em funcionamento), para que uma linha confirmada continue válida depois que a história sai da janela de 7 dias. A CI falha uma linha cujo id não se resolve por nenhum desses caminhos. Enquanto esse arquivo de ids não existir, nenhuma linha com rótulo REAL, OVERHYPED, FALSE ou PUSHED é adicionada, porque uma linha cuja história saísse da janela de 7 dias não teria a que se resolver.

Os quatro feeds (`web/feed.xml`, `web/feed.json`, `web/feed.pt.xml`, `web/feed.pt.json`) mostram o rótulo de cada linha, e as páginas leem o nosso próprio texto de duas tabelas geradas a partir de `web/i18n/strings.json` (`web/i18n/table.en.json`, `web/i18n/table.pt.json`). Por isso, um pull request que altera `web/verdicts.json` ou `web/i18n/strings.json` roda `npm ci --prefix scripts/dehype --ignore-scripts && node scripts/dehype/compose.mjs` e inclui os quatro feeds e as duas tabelas no mesmo commit; caso contrário a CI falha (`tests/test_feed.py`). A atualização diária gera os feeds de novo depois de reaplicar o seu commit sobre `dev`.

<a id="reply"></a>
## Direito de resposta

Quem for objeto de uma história ou de um veredito (uma empresa, um projeto, o autor de uma alegação) pode responder, sem custo. O dehype respeita o direito de resposta ou retificação da Lei 13.188/2015, exercido em até 60 dias da publicação.

Como responder: envie o texto da resposta com o id da história (`s:...`) ou o link da história, por e-mail para felipe@namastex.ai, ou como issue em https://github.com/namastex888/dehype/issues (as issues são públicas).

O que acontece: a resposta entra no registro de correções como uma entrada `reply`, no idioma em que foi enviada, ligada à história que responde, e deve aparecer onde quer que o veredito dessa história apareça. Uma resposta válida é publicada em até 7 dias do recebimento. Se a resposta mostrar que um veredito está errado, o veredito é corrigido como abaixo.

<a id="corrections"></a>
## Correções

O registro de correções é `web/corrections.json`. Ele só recebe acréscimos, nunca edições: a CI compara o arquivo com o commit de base de cada mudança e falha uma mudança que edite ou remova uma entrada existente. A correção de uma entrada anterior é uma nova entrada.

Cada entrada tem um id (`c:1`, `c:2`, ... em ordem), uma data, um tipo (`correction` ou `reply`), a história a que se refere (`s:...`, quando se refere a uma), o texto (uma correção em inglês e português; uma resposta no idioma em que foi enviada) e um link opcional.

Quando um veredito muda, a linha em `web/verdicts.json` é alterada por um pull request e uma entrada de correção diz o que mudou e por quê. O estado anterior fica no histórico público do git. Para apontar um erro, use o mesmo e-mail ou issue de uma resposta.

<a id="removals"></a>
## Pedidos de remoção e posts apagados

Como pedir a remoção: envie o endereço (URL) do post por e-mail para felipe@namastex.ai. Uma issue em https://github.com/namastex888/dehype/issues também serve, mas as issues são públicas, então a própria issue apontaria para o post. Qualquer pessoa pode pedir sobre um post que escreveu ou que lhe diz respeito.

O que acontece: o responsável registra um pedido aceito em `web/removals.json` por um pull request. Esse arquivo é revisado pelo responsável: a atualização diária nunca o escreve, e a verificação dos arquivos do responsável (`scripts/check_owner_files.py`) recusa um commit da atualização que o altere. Uma entrada guarda só o hash SHA256 do endereço do post e a data em que o pedido foi aceito. Um hash não mostra o endereço diretamente, mas quem já tem o endereço, ou consegue listar endereços candidatos (os endereços do Hacker News e do Reddit seguem um padrão numerado), pode calcular o mesmo hash e reconhecê-lo. O mesmo pull request também roda `python3 hype_build.py --scrub web/hype.json` e inclui o resultado, para que a página Hype retire de imediato um post do dossiê de pesquisa; a CI falha um pull request de remoção que deixe um post assim em `web/hype.json`.

O que a reconstrução diária retira: na reconstrução diária seguinte (a CI aplica um pedido a `pulse.json` e `briefing.json` gerados num dia posterior à data do pedido), um post que `web/removals.json` nomeia, ou que a sua fonte informa como apagado ou removido, sai das páginas, de `pulse.json`, de `briefing.json`, dos feeds e da base histórica que o pipeline mantém. Um post do dossiê de pesquisa também sai de `web/hype.json` e da página Hype, e nenhuma execução posterior o traz de volta.

A reverificação de posts apagados: os coletores são buscas e linhas do tempo que nunca informam uma exclusão, então cada atualização diária consulta pelo id cada post guardado que as saídas do dia podem mostrar: o Hacker News pelo endpoint de item do Firebase (`deleted` ou `dead`), o Mastodon por `/api/v1/statuses/<id>` do mastodon.social (um 404, também quando a verificação de renderização do Mastodon o registra), o Bluesky por `app.bsky.feed.getPosts` (um post ausente da resposta) e os registros do Reddit pelo arquivo arctic-shift, por id (o texto ou o título do post diz `[deleted]` ou `[removed]`, ou o arquivo registra uma categoria de remoção; o Reddit aparece só como contagem, então um registro assim sai das contagens). Ela consulta também cada post do dossiê de pesquisa que guarda um id de origem (hoje os seus posts do Hacker News). Um post do dossiê encontrado apagado é registrado em `web/checks/dossier-gone.json`, escrito pela atualização, que só recebe acréscimos e nunca é editado e guarda só o hash SHA256 do endereço de cada post assim (reconhecível, como acima, por quem tem ou consegue listar o endereço); a atualização então retira o post de `web/hype.json` (só remoção). A reverificação roda com um limite de tempo de 180 segundos e falha fechada: um post que ela não conseguiu consultar naquele dia aparece só como contagem, nunca com o seu texto ou link, até que uma execução posterior o consulte.

O hash: o SHA256, em hexadecimal minúsculo, do endereço do post exatamente como a fonte o dá: `https://news.ycombinator.com/item?id=<id>` para o Hacker News; para o Mastodon o endereço próprio do post ou `https://mastodon.social/statuses/<id>`; `https://bsky.app/profile/<conta>/post/<id>` para o Bluesky; o permalink `https://www.reddit.com/r/...` para o Reddit. Ele pode ser calculado com `printf '%s' '<endereço>' | shasum -a 256`.

Os posts do X, LinkedIn, YouTube e Telegram no dossiê de pesquisa não guardam endereço, texto nem autor: nada de um post assim é mostrado, então não há nada a reverificar nem a nomear.

Limites: o histórico do git já publicado e os manifestos ancorados não podem ser editados. Um post publicado antes da sua remoção fica nos commits anteriores deste repositório público e em qualquer manifesto já ancorado, como acontece com o hash dos registros do Reddit; a remoção vale a partir da reconstrução diária seguinte.

<a id="file-shapes"></a>
## Formato dos arquivos

O formato de `web/verdicts.json` e de `web/corrections.json`, com exemplos, está na versão em inglês: [POLICY.md](POLICY.md#file-shapes).

`web/removals.json` (revisado pelo responsável; uma entrada por pedido aceito):

```json
{"entries": [
  {"sha256": "<SHA256 do endereço do post, 64 hexadecimais minúsculos>", "date": "2026-10-20"}
]}
```

`web/checks/dossier-gone.json` (escrito pela atualização, só recebe acréscimos; uma entrada por post do dossiê encontrado apagado):

```json
{"note": "...", "gone": [{"sha256": "<SHA256 do endereço do post como guardado em web/hype.json>", "found": "2026-10-20"}]}
```
