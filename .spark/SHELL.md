# Spark Shell — studylog-agent

## Protocol
Version: 1.0 | Storage: `.spark/` directory

## What is studylog-agent
Tracks learning progress, study sessions, and knowledge acquisition.
Part of the Cocapn Fleet — student domain agent with explicit PLATO tile schema.

## Rooms
- **domain/** — what this agent does (learning, study)
- **lessons/** — learning experiences, study results
- **active/** — current study sessions
- **decisions/** — learning strategy choices
- **questions/** — what to learn next

## Connection to Fleet
Bootstrap Spark → Bootstrap Bomb → PLATO → greenhorn → studylog-agent
PLATO tile schema: explicit (see agent docs)

See: github.com/SuperInstance/studylog-agent
