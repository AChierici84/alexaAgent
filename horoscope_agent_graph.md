# Grafo Agente Oroscopo

```mermaid
%%{init: {'flowchart': {'curve': 'linear'}}}%%
graph TD;
	__start__([<p>__start__</p>]):::first
	extract(extract)
	fetch_horoscope(fetch_horoscope)
	translate(translate)
	__end__([<p>__end__</p>]):::last
	__start__ --> extract;
	translate --> __end__;
	extract -. &nbsp;fetch&nbsp; .-> fetch_horoscope;
	extract -. &nbsp;end&nbsp; .-> __end__;
	fetch_horoscope -.-> translate;
	fetch_horoscope -. &nbsp;end&nbsp; .-> __end__;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc

```
