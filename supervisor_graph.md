# Grafo Supervisore Multiagente

Questo grafo mostra il flusso del supervisore che coordina i vari agenti:

```mermaid
%%{init: {'flowchart': {'curve': 'linear'}}}%%
graph TD;
	__start__([<p>__start__</p>]):::first
	router(router)
	weather_agent(weather_agent)
	unsupported(unsupported)
	__end__([<p>__end__</p>]):::last
	__start__ --> router;
	unsupported --> __end__;
	weather_agent --> __end__;
	router -.-> weather_agent;
	router -.-> unsupported;
	router -. &nbsp;end&nbsp; .-> __end__;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc

```
