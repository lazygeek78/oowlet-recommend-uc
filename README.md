# oowlet-recommend-uc

Recommendation Intelligence for Oowlet: two engines on one shared intelligence layer.

- **Content Recommendation Engine** — what should this member see?
- **People Recommendation Engine** — who should this member connect with?

Both engines read users and content only through the shared layer
(`ruc/intelligence/hub.py`). They share embeddings, affinities, history and
the feedback loop, and differ in their candidate sources and ranking.

```
User ─▶ Candidate Generation ─▶ Candidate Pool ─▶ Eligibility ─▶ Ranking ─▶ Diversity ─▶ Recommendations
            │                                    (policy, trust,   (weighted   (MMR, caps,     │
            ├ collaborative (item-item)           privacy, age,     score or    exploration)    │
            ├ matrix factorization (ALS)          audience, safety, logistic,                   │
            ├ content similarity (vectors)        already seen)     context-                    │
            ├ behavioral similarity                                 aware)                      │
            ├ social graph · trending · fresh                                                   │
            ├ followed creators · interest topics                                               │
            └ contextual (topic, community, seed, session)                                      ▼
  ◀── Model evaluation ◀── Feature update ◀── Event collection ◀── Behavior ◀───────────────── User
```

## Design

| Your design | Where |
|---|---|
| Signals IMPRESSION → CLICK → OPEN → VIEW → WATCH TIME → COMPLETION → LIKE → COMMENT → SHARE → SAVE → FOLLOW → PURCHASE → OUTCOME | `ruc/signals.py`: weighted by funnel depth, plus negatives (skip, hide, report, unfollow); watch time from dwell and watch fraction |
| User profile: explicit, behavioral, historical, contextual preferences, user embedding | `UserState` in `ruc/intelligence/hub.py` |
| Time-aware history | exponential decay: 6 h (session), 7 d (behavioral), 90 d (historical) |
| Candidate generation | `ruc/candidates/generators.py`: 10 content sources, 7 people sources |
| Recommendation score = interest + relevance + behavioral + context + quality + credibility + freshness + social + trend + creator − repetition − negative feedback | `ruc/ranking/features.py` (components) and `ruc/ranking/models.py` (weights) |
| Start weighted, train a ranking model later | `WeightedRanker`, then `LogisticRanker` trained from the serve log (`ruc/training/trainer.py`), with an A/B challenger and promotion only when AUC improves |
| Context: session, location, device, time, activity, current topic, community, recent interactions | `ruc/context.py` |
| Policy / trust / diversity | `ruc/policy/eligibility.py`, `ruc/policy/diversity.py` |
| Feature store: works with the feature management module | `ruc/intelligence/feature_client.py` reads content features (embeddings, topics, entities, sentiment, intent, category, quality, credibility, visual / audio / semantic vectors) from oowlet-feature-service and writes the engine's user embedding and affinities back |
| Feedback loop | `ruc/app.py`: engagement attributed to the serve it came from (`recommendation_id`), per-variant metrics, periodic retraining |
| Model stack | Collaborative filtering, implicit-ALS matrix factorization, vector search and graph proximity are built in. LightGBM, two-tower, GraphSAGE / LightGCN and LLM features plug in behind the same interfaces (`Ranker.score`, a candidate source, `Embedder`) |
| Embeddings | `hashing-v1` built in; any sentence-transformers model (BGE, E5) with `RUC_INTELLIGENCE__EMBEDDING_MODEL` when that package is installed |

## Privacy and safety

These rules are enforced in code and covered by tests:

- **Filtering happens before ranking.** Privacy, blocks (either side, by graph edge or in preferences), age, audience, visibility, safety labels and trust are checked first. `CheckEligibility` runs the same rules. A later page and Explain re-check them, so a block takes effect immediately.
- **Age:**
  - Adults and minors are never suggested to each other. Unknown age counts as a minor.
  - Adult-only content never reaches a minor, and reaches an adult only when they set mature content.
  - Content with no audience information (legacy posts) reaches adults only.
- **Sensitive topics** (health, religion, politics, sexuality, …; see `RUC_POLICY__SENSITIVE_TOPIC_PREFIXES`):
  - They are never inferred from behaviour, not even as dislikes.
  - They count only when the user declared them and allowed it.
  - They are never shown to anyone else.
- **Another person's data is shown only with their consent:**
  - Their activity (the engagers list, "your network engaged" evidence, interests learned from their activity) requires `show_activity_to_others`.
  - Mutual connections are computed only through people who allow that signal, including the person at the far end.
- **Opt-outs:**
  - `personalization_enabled=false` means popularity and editorial results only.
  - `use_engagement_history=false` means only declared preferences are used.
  - `contribute_to_collaborative=false` keeps the user out of co-engagement, similar-users results and matrix-factorization training.
  - `discoverable_in_suggestions=false` means the user is never suggested to anyone.
- **Erasure:** `DeleteUserData` erases the user's events, profile, serves, feedback, caches, page tokens and model rows, and publishes `recommenduc.user.data_erased`. The feature service's API has no delete, so it should act on that event.
- **Identity** comes from the bearer token only (`RUC_AUTH__TOKENS_FILE`, stored as hashes). Every RPC checks its own-user or scope rule (`proto/recommenduc/service.proto`).

## Build and run

```bash
make build                     # venv, protos (../proto), checks, dist/oowlet-recommend-uc + wheel
dist/oowlet-recommend-uc check # configuration, event layer and feature service reachable
dist/oowlet-recommend-uc       # gRPC API + event consumer
make test                      # 31 tests, including gRPC end to end and the real CLI process
```

Configuration is through `RUC_*` variables; every setting is in `.env.example`. Ranking weights per engine and surface can be overridden with `RUC_RANKING__WEIGHTS_FILE` (see `weights.example.json`).

**Protos.** `make proto` compiles three sets from `../proto`:

- `recommenduc/`: the API and events
- `eventlayer/`: the broker and legacy events
- `feature_service/`: the feature service client

**Events.**

- Consumed: `recommenduc.engagement.recorded`, `.content.changed`, `.graph.changed` and `.profile.changed`, plus the legacy `PostEngagementEvent`, `BehaviorUpdatedEvent` and `PostCreated/DeletedEvent`.
- Published: `recommenduc.recommendation.served`, `.feedback.received` and `.user.data_erased`.
- Restrict publishing to these topics with broker ACLs.

## Limits

- **Storage is in memory** (`ruc/store/memory.py`): one instance, and state is lost on restart. Everything goes through the `Store` interface (`ruc/store/base.py`), so a persistent backend replaces it without touching the engines. That backend could be this module's own database, or the core's data path as the dataset curator uses. Choosing it is the main open decision.
- **Scale of the built-in algorithms:**
  - Vector search is exact (`ruc/intelligence/vector_index.py`), good up to a few million vectors; swap in HNSW or FAISS beyond that.
  - Matrix factorization is dense numpy, for up to a few hundred thousand users × items.
- **Training data** comes from the serve log. With the in-memory store, run training inside the server (`RUC_TRAINING__INTERVAL_MINUTES`).
- **Page tokens** belong to the instance that served page 1, for 30 minutes.


I wanted to design the recommendation engine for content and user based on which the content fetched as per user preferences. Similarly for user. My intent is to create recommendation engine for selecting content and user to whom a member can be connected to. 
Here in this code it should track engagement around content and it should also track the users data and his preferences to find whether particular content can be recommended to the given user or not. it should able to see history data of related content and other users , and many more. So can you guide me how I will design the recommendation engine. 
dual recommendation platform inside Oowlet AI:
Content Recommendation Engine — What content should this member see?
People Recommendation Engine — Which people should this member connect with?

The important part is that these should share the same user intelligence, behavioral data, embeddings, feedback loop , while having different candidate-generation and ranking logic.

The recommendation engines should not independently build an understanding of users or content. They should consume a shared intelligence layer.

Oowlet then determines:
What are the best candidates for this particular user, at this particular time, in this particular context?
User
 │
 ▼
Candidate Generation
 │
 ├── Collaborative Filtering
 ├── Content Similarity
 ├── Behavioral Similarity
 ├── Social Graph
 ├── Trending
 ├── Fresh Content
 ├── Followed Creators
 └── Contextual Candidates
 │
 ▼
Candidate Pool
 │
 ▼
Ranking Model
 │
 ▼
Policy / Trust / Diversity
 │
 ▼
Final Recommendations

The signals which is collected are 
IMPRESSION
    ↓
CLICK
    ↓
OPEN
    ↓
VIEW
    ↓
WATCH TIME
    ↓
COMPLETION
    ↓
LIKE
    ↓
COMMENT
    ↓
SHARE
    ↓
SAVE
    ↓
FOLLOW
    ↓
PURCHASE
    ↓
OUTCOME

Oowlet need to generate:
	•	embeddings
	•	topics
	•	entities
	•	sentiment
	•	intent
	•	content category
	•	quality
	•	credibility
	•	behavioral signals
	•	visual features
	•	audio features
	•	semantic features
The recommendation engine consumes those features.
1. You need to generate candidate. 
2. After candidate generation, you calculate a recommendation score.
Recommendation Score =
    User Interest
  + Content Relevance
  + Behavioral Affinity
  + Context Relevance
  + Quality
  + Credibility
  + Freshness
  + Social Signal
  + Trend Signal
  + Creator Affinity
  - Repetition
  - Negative Feedback

Initially you can use a weighted scoring system.
Later you train a ranking model.
Context should modify the recommendation
Context to include 
User
├── historical preferences
├── current session
├── location
├── device
├── time
├── activity
├── current topic
├── current community
└── recent interactions

This is contextual recommendation, and it fits very well with your Human Intelligence architecture.
Oowlet Recommendation Feature Store I will integrate to feature management module. This module should able to collaborate with feature management module. 

maintain an embedding representation of the user's interests.
User Profile
     │
     ├── Explicit Preferences
     ├── Behavioral Preferences
     ├── Historical Preferences
     ├── Contextual Preferences
     └── User Embedding
Historical data should be time-aware

Feedback loop 
                 Recommendation
                       │
                       ▼
                     User
                       │
                       ▼
                   Behavior
                       │
                       ▼
                Event Collection
                       │
                       ▼
                 Feature Update
                       │
                       ▼
                Model Evaluation
                       │
                       ▼
             Recommendation Model
                       │
                       └──────────────→

The model stack

Candidate generation
	•	Collaborative filtering
	•	Matrix factorization
	•	Two-tower retrieval
	•	Approximate nearest-neighbor/vector search
	•	Graph-based recommendation
	•	Content-based retrieval
Ranking
	•	Logistic regression initially
	•	Gradient boosted trees
	•	XGBoost / LightGBM
	•	Deep ranking models
	•	Wide & Deep
	•	DeepFM
	•	DLRM-style architectures
Embeddings
	•	Sentence Transformers
	•	BGE
	•	E5
	•	domain-specific embedding models
Graph
For people recommendation:
	•	graph embeddings
	•	GraphSAGE
	•	LightGCN
	•	GAT
LLMs
Use LLMs where they add value:
	•	semantic understanding
	•	cold-start content
	•	intent interpretation
	•	explanation
	•	feature extraction
	•	query understanding

the recommendation engine isn't just consuming Human Intelligence; it is continuously generating new behavioral intelligence about how people discover, choose, connect, engage and decide.
I would therefore make Recommendation Intelligence one of the major AI services inside Oowlet AI, with Content Recommendation and People Recommendation as two specialized engines sharing one common User/Content Intelligence and Feature Platform.


