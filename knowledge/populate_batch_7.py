import os
from pathlib import Path

BASE_DIR = Path("knowledge/skills")

TEMPLATE = """---
name: "{name}"
description: "{description}"
domain: "{domain}"
tags: {tags}
---

# Role
{role}

## Core Concepts
{concepts}

## Reasoning Framework
{framework}

## Output Standards
{standards}
"""

SKILLS = [
    # ==========================
    # DATA ENGINEERING & BIG DATA
    # ==========================
    {
        "filename": "data/spark_engineer.md",
        "name": "Apache Spark Engineer",
        "description": "Expertise in distributed data processing, RDDs, and DataFrames.",
        "domain": "data",
        "tags": ["big-data", "spark", "scala", "python"],
        "role": "You process petabytes in memory.",
        "concepts": "- **Lazy Evaluation**: Transformations are not executed until an Action is called.\n- **Shuffle**: Moving data between nodes (expensive).\n- **Partitioning**: Splitting data for parallelism.",
        "framework": "1. **Driver**: Orchestrate the job.\n2. **Executor**: Workers doing the task.\n3. **DAG**: Directed Acyclic Graph of stages.",
        "standards": "- Minimize **Data Skew**."
    },
    {
        "filename": "data/kafka_engineer.md",
        "name": "Kafka Streaming Engineer",
        "description": "Expertise in real-time event streaming, KSQL, and Connect.",
        "domain": "data",
        "tags": ["streaming", "kafka", "java", "real-time"],
        "role": "You handle millions of events per second.",
        "concepts": "- **Log Compaction**: Keeping only the latest value for a key.\n- **Consumer Groups**: Scaling consumption horizontally.\n- **Exactly-Once**: The holy grail of delivery semantics.",
        "framework": "1. **Producer**: Send message (Key/Value).\n2. **Broker**: Store on disk.\n3. **Consumer**: Read and process.",
        "standards": "- Monitor **Consumer Lag**."
    },
    {
        "filename": "data/snowflake_architect.md",
        "name": "Snowflake Data Architect",
        "description": "Expertise in cloud data warehousing, zero-copy cloning, and snowpipe.",
        "domain": "data",
        "tags": ["data-warehouse", "snowflake", "sql", "cloud"],
        "role": "You decouple storage from compute.",
        "concepts": "- **Micro-partitions**: Automatic clustering of data.\n- **Time Travel**: Querying data as it was 24 hours ago.\n- **Virtual Warehouses**: Resizable compute clusters.",
        "framework": "1. **Stage**: Load files to S3/Internal.\n2. **Copy Into**: Ingest into tables.\n3. **Task**: Schedule SQL jobs.",
        "standards": "- Use **Transient Tables** for temporary data."
    },
    {
        "filename": "data/nosql_architect.md",
        "name": "NoSQL Database Architect",
        "description": "Expertise in DynamoDB, MongoDB, Cassandra, and CAP theorem trade-offs.",
        "domain": "data",
        "tags": ["database", "nosql", "mongodb", "cassandra"],
        "role": "You choose the right tool for the data shape.",
        "concepts": "- **Document Store**: JSON blobs (Mongo).\n- **Wide Column**: Sparse rows (Cassandra).\n- **Key-Value**: Hash map at scale (Redis/Dynamo).",
        "framework": "1. **Access Pattern**: How will you query it?\n2. **Partition Key**: Distributing the load.\n3. **Consistency**: Eventual vs Strong.",
        "standards": "- Avoid **Hot Partitions**."
    },
    {
        "filename": "data/graph_db_expert.md",
        "name": "Graph Database Expert (Neo4j)",
        "description": "Expertise in relationship-heavy data, Cypher queries, and graph algo.",
        "domain": "data",
        "tags": ["database", "graph", "neo4j", "relationships"],
        "role": "You see the world as nodes and edges.",
        "concepts": "- **Index-Free Adjacency**: Traversing is fast because pointers are stored.\n- **Nodes**: Entities.\n- **Edges**: Relationships (with properties).",
        "framework": "1. **Model**: Whiteboard the connections.\n2. **Ingest**: Load CSVs as nodes.\n3. **Query**: MATCH (n)-[r]->(m) RETURN n.",
        "standards": "- Use **Labels** effectively."
    },

    # ==========================
    # ARTIFICIAL INTELLIGENCE & ML (ADVANCED)
    # ==========================
    {
        "filename": "ai/reinforcement_learning.md",
        "name": "Reinforcement Learning Researcher",
        "description": "Expertise in agents, environments, rewards, and policy optimization.",
        "domain": "ai",
        "tags": ["ai", "rl", "ml", "agents"],
        "role": "You train agents to play the game of life.",
        "concepts": "- **Exploration vs Exploitation**: Try new things vs do what works.\n- **Reward Function**: Designing the goal is the hardest part.\n- **Q-Learning**: Learning the value of action A in state S.",
        "framework": "1. **Observation**: Agent sees state.\n2. **Action**: Policy decides move.\n3. **Reward**: Environment feedback.",
        "standards": "- Watch for **Reward Hacking**."
    },
    {
        "filename": "ai/gan_specialist.md",
        "name": "Generative Adversarial Network (GAN) Specialist",
        "description": "Expertise in generating synthetic data, images, and creative AI.",
        "domain": "ai",
        "tags": ["ai", "gan", "generative", "deep-learning"],
        "role": "You pit two neural nets against each other.",
        "concepts": "- **Generator**: Creates fakes.\n- **Discriminator**: Detects fakes.\n- **Mode Collapse**: Generator produces only one type of output.",
        "framework": "1. **Train Discriminator**: On real data + fake data.\n2. **Train Generator**: Try to fool frozen Discriminator.\n3. **Loop**: Until equilibrium.",
        "standards": "- Check **Inception Score**."
    },
    {
        "filename": "ai/mlops_engineer.md",
        "name": "MLOps Engineer",
        "description": "Expertise in model deployment, monitoring, experiment tracking (MLflow).",
        "domain": "ai",
        "tags": ["mlops", "devops", "ml", "deployment"],
        "role": "You take models out of notebooks and into production.",
        "concepts": "- **Data Drift**: Input distribution changes over time.\n- **Concept Drift**: The relationship between input and output changes.\n- **Feature Store**: Central repository for model inputs.",
        "framework": "1. **Train**: CI/CD for models.\n2. **Deploy**: REST API (Seldon/TFServing).\n3. **Monitor**: Accuracy/Latency.",
        "standards": "- Version **Data** and **Code** together."
    },
    {
        "filename": "ai/nlp_transformer_expert.md",
        "name": "Transformer Architecture Expert",
        "description": "Expertise in Attention mechanisms, BERT, GPT, and fine-tuning.",
        "domain": "ai",
        "tags": ["nlp", "transformers", "bert", "gpt"],
        "role": "You understand that Attention Is All You Need.",
        "concepts": "- **Self-Attention**: Weighing the importance of words in context.\n- **Positional Encoding**: Injecting order into parallel processing.\n- **Fine-Tuning**: Adapting a pre-trained giant to a specific task.",
        "framework": "1. **Pre-train**: Masked Language Modeling.\n2. **Fine-tune**: Classification/NER.\n3. **Inference**: Beam Search decoding.",
        "standards": "- Manage **Tokenizer** vocabulary."
    },
    {
        "filename": "ai/computer_vision_segmentation.md",
        "name": "Image Segmentation Expert",
        "description": "Expertise in U-Net, Mask R-CNN, and pixel-level classification.",
        "domain": "ai",
        "tags": ["cv", "segmentation", "images", "medical-imaging"],
        "role": "You classify every single pixel.",
        "concepts": "- **Semantic vs Instance**: Is it 'a car' or 'car #1'?\n- **IoU**: Intersection over Union (The metric).\n- **Encoder-Decoder**: Bottleneck architecture.",
        "framework": "1. **Labeling**: Polygons around objects.\n2. **Augmentation**: Elastic deformations.\n3. **Training**: Dice Loss function.",
        "standards": "- Handle **Class Imbalance**."
    },
    
    # ==========================
    # SYSTEMS PROGRAMMING & HPC
    # ==========================
    {
        "filename": "coding/hpc_engineer.md",
        "name": "High Performance Computing (HPC) Engineer",
        "description": "Expertise in MPI, OpenMP, and supercomputer clusters.",
        "domain": "coding",
        "tags": ["hpc", "supercomputing", "c++", "mpi"],
        "role": "You simulate the universe.",
        "concepts": "- **MPI**: Message Passing Interface (Inter-node).\n- **OpenMP**: Multi-threading (Intra-node).\n- **SIMD**: Single Instruction Multiple Data (Vectorization).",
        "framework": "1. **Decomposition**: Domain vs Functional.\n2. **Communication**: Minimize latency.\n3. **Synchronization**: Avoid barriers.",
        "standards": "- Optimize **Cache Locality**."
    },
    {
        "filename": "coding/driver_developer.md",
        "name": "Kernel/Driver Developer",
        "description": "Expertise in Linux Kernel modules, Windows drivers, and DMA.",
        "domain": "coding",
        "tags": ["kernel", "driver", "c", "low-level"],
        "role": "You are the bridge between software and hardware.",
        "concepts": "- **User Space vs Kernel Space**: The protection rings (Ring 0 vs Ring 3).\n- **DMA**: Direct Memory Access (Bypassing CPU).\n- **IRQ**: Interrupt Requests.",
        "framework": "1. **Probe**: Detect hardware.\n2. **Init**: Setup resources.\n3. **IOCTL**: Handle user commands.",
        "standards": "- **Never Panic** the kernel."
    },
    {
        "filename": "coding/compiler_engineer.md",
        "name": "Compiler Engineer (LLVM)",
        "description": "Expertise in lexing, parsing, IR optimization, and code generation.",
        "domain": "coding",
        "tags": ["compiler", "llvm", "pl-theory", "c++"],
        "role": "You translate thought into machine code.",
        "concepts": "- **AST**: Abstract Syntax Tree.\n- **SSA**: Static Single Assignment form (IR).\n- **Optimization Passes**: Dead code elimination, loop unrolling.",
        "framework": "1. **Frontend**: Lex/Parse -> AST.\n2. **Middle-end**: AST -> IR -> Optimize.\n3. **Backend**: IR -> Asm (x86/ARM).",
        "standards": "- Correctness > Performance."
    }
]

def create_skills():
    print(f"Generating {len(SKILLS)} skills (Batch 7)...")
    for skill in SKILLS:
        filepath = BASE_DIR / skill['filename']
        
        # Ensure dir exists
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        content = TEMPLATE.format(
            name=skill['name'],
            description=skill['description'],
            domain=skill['domain'],
            tags=str(skill['tags']),
            role=skill['role'],
            concepts=skill['concepts'],
            framework=skill['framework'],
            standards=skill['standards']
        )
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Created: {filepath}")

if __name__ == "__main__":
    create_skills()
