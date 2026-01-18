# Grafo Agente Calcolatore

```mermaid
%%{init: {'flowchart': {'curve': 'linear'}}}%%
graph TD;
	__start__([<p>__start__</p>]):::first
	extract(extract)
	calculate(calculate)
	format(format)
	__end__([<p>__end__</p>]):::last
	__start__ --> extract;
	format --> __end__;
	extract -.-> calculate;
	extract -.-> __end__;
	calculate -.-> format;
	calculate -.-> __end__;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc

```
