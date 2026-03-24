CLI Commands

- agent-breaker init
	- Initializes a breaker.yaml config file
	- Options:
		--force   Overwrite existing breaker.yaml if present

- agent-breaker run
	- Runs Agent Breaker with the specified config
	- Options:
 - 
		--debug         Show full traceback on errors
		--full-output   Show full payload and model response text
   
	- Environment variables (optional, default is off):
		AGENT_BREAKER_DEBUG=1        Enable debug mode (default: off)
		AGENT_BREAKER_FULL_OUTPUT=1  Enable full output (default: off)
