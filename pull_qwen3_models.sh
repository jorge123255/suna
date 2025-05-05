#!/bin/bash
# Script to pull Qwen3 models from Ollama

# Configuration
OLLAMA_API_BASE="http://192.168.1.10:11434"

# Color codes for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Qwen3 models to pull
MODELS=(
    # Base models
    "qwen3:8b"       # 8B parameter model
    "qwen3:14b"      # 14B parameter model
    "qwen3:32b"      # 32B parameter model
    
    # Instruct models (for chat)
    "qwen3:8b-instruct"
    "qwen3:14b-instruct"
    "qwen3:32b-instruct"
)

echo -e "${BLUE}Checking for installed models on ${OLLAMA_API_BASE}...${NC}"

# Get list of installed models
INSTALLED_MODELS=$(curl -s "${OLLAMA_API_BASE}/api/tags")

if [ $? -ne 0 ]; then
    echo -e "${RED}Could not connect to Ollama server at ${OLLAMA_API_BASE}${NC}"
    echo "Please check if the server is running and accessible."
    exit 1
fi

echo -e "\n${BLUE}Currently installed models:${NC}"
echo "$INSTALLED_MODELS" | grep -o '"name":"[^"]*"' | sed 's/"name":"//g' | sed 's/"//g' | while read -r model; do
    echo -e "- ${GREEN}$model${NC}"
done

echo -e "\n${BLUE}Checking for Qwen3 models...${NC}"
MODELS_TO_PULL=()

for model in "${MODELS[@]}"; do
    if echo "$INSTALLED_MODELS" | grep -q "\"name\":\"$model\""; then
        echo -e "✓ ${GREEN}$model${NC} is already installed"
    else
        echo -e "✗ ${RED}$model${NC} is not installed"
        MODELS_TO_PULL+=("$model")
    fi
done

if [ ${#MODELS_TO_PULL[@]} -eq 0 ]; then
    echo -e "\n${GREEN}All Qwen3 models are already installed!${NC}"
else
    echo -e "\n${YELLOW}Need to pull ${#MODELS_TO_PULL[@]} models:${NC}"
    for model in "${MODELS_TO_PULL[@]}"; do
        echo -e "- ${YELLOW}$model${NC}"
    done
    
    echo -e "\n${BLUE}Starting model pulls...${NC}"
    for model in "${MODELS_TO_PULL[@]}"; do
        echo -e "\n${BLUE}Pulling model: $model...${NC}"
        curl -X POST "${OLLAMA_API_BASE}/api/pull" -d "{\"name\":\"$model\"}"
        if [ $? -eq 0 ]; then
            echo -e "\n${GREEN}Successfully pulled $model${NC}"
        else
            echo -e "\n${RED}Failed to pull $model${NC}"
        fi
    done
fi

echo -e "\n${BLUE}Updating task classifier with new models...${NC}"

# Update task classifier with new models
TASK_CLASSIFIER_PATH="/Volumes/appdata/suna/backend/services/task_classifier.py"
EMBEDDING_CLASSIFIER_PATH="/Volumes/appdata/suna/backend/services/embedding_task_classifier.py"

# Update the task classifier
if [ -f "$TASK_CLASSIFIER_PATH" ]; then
    # Create a backup
    cp "$TASK_CLASSIFIER_PATH" "${TASK_CLASSIFIER_PATH}.bak"
    
    # Update the TASK_MODELS dictionary
    sed -i '' 's/TASK_MODELS = {/TASK_MODELS = {\n    "coding": "qwen3:14b-instruct",     # Qwen3 coding model\n    "reasoning": "mixtral:8x22b-instruct-v0.1-q4_K_M", # Powerful reasoning model\n    "creative": "qwen3:8b-instruct",                   # Qwen3 creative model\n    "general": "qwen3:32b-instruct",                  # Qwen3 general model/' "$TASK_CLASSIFIER_PATH"
    
    echo -e "${GREEN}Updated $TASK_CLASSIFIER_PATH with new model mappings${NC}"
fi

# Update the embedding classifier if it exists
if [ -f "$EMBEDDING_CLASSIFIER_PATH" ]; then
    # Create a backup
    cp "$EMBEDDING_CLASSIFIER_PATH" "${EMBEDDING_CLASSIFIER_PATH}.bak"
    
    # Update the TASK_MODELS dictionary
    sed -i '' 's/TASK_MODELS = {/TASK_MODELS = {\n    "coding": "qwen3:14b-instruct",     # Qwen3 coding model\n    "reasoning": "mixtral:8x22b-instruct-v0.1-q4_K_M", # Powerful reasoning model\n    "creative": "qwen3:8b-instruct",                   # Qwen3 creative model\n    "general": "qwen3:32b-instruct",                  # Qwen3 general model/' "$EMBEDDING_CLASSIFIER_PATH"
    
    echo -e "${GREEN}Updated $EMBEDDING_CLASSIFIER_PATH with new model mappings${NC}"
fi

echo -e "\n${GREEN}Done!${NC}"
