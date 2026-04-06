# Inspiration

We wanted to solve the chaos of multitasking during online meetings. People constantly switch between tabs to verify facts, check data, or look up information while trying to stay engaged in discussions. That constant context-switching kills focus and efficiency. The idea for Nemo came from imagining a world where an AI could sit in the meeting as a helpful teammate, not just a note-taker after it ends.

# What It Does

Nemo is a voice-activated AI that joins your video calls as a third participant. You simply say "Hey Nemo" and it instantly listens, researches, and answers out loud in real time. It can fact-check, moderate debates, or act as a simulated customer to help teams refine their ideas. Nemo makes meetings smoother, faster, and more intelligent.

#How We Built It

We used OpenAI for language understanding, ElevenLabs for natural speech, Recall for call automation, Composio for multi-app connections, LangGraph for context retention, and Flask with NGrok to handle endpoints and streaming audio. The result is a fully working prototype that can join calls on Zoom, Google Meet, and soon Slack.

# Challenges We Ran Into

One of the biggest challenges was maintaining real-time responsiveness while processing both voice input and output without noticeable delay. Integrating multiple APIs together while keeping latency low was complex. We also had to ensure the assistant stayed secure, with no data stored or logged after meetings.

# Accomplishments That We're Proud Of

We built a working AI assistant that actually joins calls in real time, not just a background summarizer. Nemo responds instantly to natural speech and can handle multi-turn conversations. When we saw people interact with it naturally during our tests we knew that the concept was real.

# What We Learned

We learned how important timing, latency, and context are in making AI feel human. A single second of delay can break immersion, so optimizing communication between APIs was key. We also realized that people prefer voice-based AI that feels like part of the room rather than something running in another tab.

# What's Next For Nemo

Next, we plan to launch a public beta and onboard the first 1000 teams. We want to expand Nemo to more platforms like Slack and Microsoft Teams, improve customization for company specific data, and introduce personality options for different meeting styles. The long-term goal is to make Nemo the default AI teammate for every team that talks online.

# Built With

composio-mcp
elevenlabs-api
flask
google-meet
javascript
langgraph
ngrok
openai-api
python
recall-api
slack
websockets
zoom
