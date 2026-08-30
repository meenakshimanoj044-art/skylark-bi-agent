# Technical Architecture & Decision Log
**Role:** Full Stack Developer Assignment — Skylark Drones  
**Candidate:** Meenakshi Manoj  
**Project:** Monday.com Business Intelligence Agent  

---

### 1. Key Assumptions Made
* **Data Volume Scale:** It is assumed that active tracking pipelines for deals and operational work orders contain fewer than 10,000 active rows at any given time. This justifies an in-memory extraction pipeline over complex background pagination worker queues.
* **Read-Only Access Patterns:** Per the assignment guidelines, the agent functions entirely as a read-only consumer, eliminating the need to manage record locking or concurrency controls back to Monday.com.
* **OpenRouter Model Choice:** `meta-llama/llama-3.1-8b-instruct:free` was selected due to its highly competitive semantic processing performance, strict JSON/Markdown schema alignment, zero subscription cost barrier, and excellent uptime records.

### 2. Trade-offs Chosen & Technical Justifications
* **In-Memory Cache Transformation vs. Dynamic GraphQL Batching**
  * *Choice:* Download whole data structures natively into isolated Pandas DataFrames upon connection lifecycle initialization.
  * *Reasoning:* Rather than making slow, repetitive network roundtrips to Monday.com for every single user message, the application caches the raw tables locally within the session state. This makes subsequent user data processing fast and responsive.
* **LLM Context Normalization vs. Rigid Procedural Scripting**
  * *Choice:* Passing raw table fragments inside the JSON prompt payload to allow the LLM to handle mismatched string variations dynamically.
  * *Reasoning:* Traditional string manipulation scripts fail when encountering missing dates or varied column types. Generative contextual parsing handles real-world messy metrics gracefully.

### 3. Interpretation of "Leadership Updates Mode"
Senior leadership needs high-level summaries, bold financial indicators, and clean comparison tables instead of scrolling through long rows of granular database outputs. 
* *Implementation:* Added an **Executive Briefing Layer** checkbox to the UI. When toggled, it injects structured system constraints into the LLM payload. This forces the model to drop granular row entries and output aggregated metrics, absolute revenue markers, and clean markdown breakdown matrices optimized for copy-pasting onto executive briefing slides.

### 4. What I Would Do Differently With More Time
* **Vector Embeddings (RAG Architecture):** Switch from full-table serialization to semantic column chunking using an in-memory vector database (e.g., ChromaDB) to handle tracking data scales past 50,000+ rows seamlessly.
* **Interactive Charting Engines:** Integrate Plotly or Streamlit Native Charts to display dynamic visual graphs alongside text responses.
* **Bi-directional Webhooks:** Configure real-time change-listener automation routes from Monday.com back to Streamlit to update the local data state instantly without forcing cache flushes.
