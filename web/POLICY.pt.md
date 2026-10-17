# Política do dehype: vereditos, direito de resposta e correções

English: [POLICY.md](POLICY.md). Esta página é publicada antes do primeiro veredito FALSE e é verificada em cada build.

## Vereditos

O dehype rotula alegações, histórias, temas e projetos, nunca pessoas ou contas. Há cinco rótulos:

- **REAL**: uma fonte primária confirma a alegação nomeada.
- **OVERHYPED**: uma fonte primária mostra que a alegação é verdadeira só em parte, ou menor do que foi apresentada.
- **FALSE**: uma fonte primária citada contradiz a alegação nomeada.
- **PUSHED**: um documento público (um registro oficial, uma marcação de patrocínio, uma admissão) mostra uma ligação paga ou material não declarada por trás da história.
- **UNVERIFIED**: ainda não conferido com uma fonte primária.

Toda história começa como "proposta pelo pipeline, não revisada". O pipeline escreve um registro de evidência com o estado "proposed" e nenhuma palavra de rótulo; ele nunca propõe um rótulo. Só o responsável muda um rótulo, por um pull request em `web/verdicts.json`, e o merge é a confirmação. O robô da atualização diária nunca escreve esse arquivo, e a CI rejeita um commit do robô que o altere.

Uma linha com rótulo REAL, OVERHYPED, FALSE ou PUSHED traz:

- a alegação nomeada (para PUSHED, o documento);
- a URL de uma fonte primária, que nunca é um post do X, do LinkedIn ou do YouTube. Uma alegação cuja única fonte é um post do X fica UNVERIFIED; o motivo pode nomear a conta oficial e a data, sem link;
- um motivo em inglês e em português;
- o commit de confirmação e a data em que foi confirmada.

FALSE só é atribuído pelo responsável, à mão, a uma alegação nomeada, com uma fonte primária citada que a contradiz. PUSHED exige o documento público citado na linha; sinais de coordenação aparecem como "sinais de coordenação" e nunca como rótulo. Toda linha FALSE aponta para o direito de resposta e as correções abaixo (`POLICY.md#reply`).

Uma linha nomeia uma história pelo seu id (`s:` e 12 hexadecimais). O id de uma história pode mudar quando chega um post mais antigo; a atualização registra então a mudança em `web/story-aliases.json` (id antigo para id novo), e a linha a acompanha. Os ids publicados em cada dia passam a ficar num arquivo de ids (`web/ledger/ids/AAAA-MM-DD.json`, escrito quando o registro diário estiver em funcionamento), para que uma linha confirmada continue válida depois que a história sai da janela de 7 dias. A CI falha uma linha cujo id não se resolve por nenhum desses caminhos.

<a id="reply"></a>
## Direito de resposta

Quem for objeto de uma história ou de um veredito (uma empresa, um projeto, o autor de uma alegação) pode responder, sem custo. No Brasil, este é o direito de resposta ou retificação da Lei 13.188/2015, exercido em até 60 dias da publicação.

Como responder: envie o texto da resposta com o id da história (`s:...`) ou o link da história, por e-mail para felipe@namastex.ai, ou como issue em https://github.com/namastex888/dehype/issues (as issues são públicas).

O que acontece: a resposta entra no registro de correções como uma entrada `reply`, no idioma em que foi enviada, ligada à história que responde, e deve aparecer onde quer que o veredito dessa história apareça. A resposta é publicada em até 7 dias do recebimento. Se a resposta mostrar que um veredito está errado, o veredito é corrigido como abaixo.

<a id="corrections"></a>
## Correções

O registro de correções é `web/corrections.json`. Ele só recebe acréscimos, nunca edições: a CI compara o arquivo com o commit de base de cada mudança e falha uma mudança que edite ou remova uma entrada existente. A correção de uma entrada anterior é uma nova entrada.

Cada entrada tem um id (`c:1`, `c:2`, ... em ordem), uma data, um tipo (`correction` ou `reply`), a história a que se refere (`s:...`, quando se refere a uma), o texto (uma correção em inglês e português; uma resposta no idioma em que foi enviada) e um link opcional.

Quando um veredito muda, a linha em `web/verdicts.json` é alterada por um pull request e uma entrada de correção diz o que mudou e por quê. O estado anterior fica no histórico público do git. Para apontar um erro, use o mesmo e-mail ou issue de uma resposta.

## Formato dos arquivos

O formato de `web/verdicts.json` e de `web/corrections.json`, com exemplos, está na versão em inglês: [POLICY.md](POLICY.md#file-shapes).
