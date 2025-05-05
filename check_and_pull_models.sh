#!/bin/bash
# Script to check for installed Ollama models and pull required models if they're not already installed

# Configuration
OLLAMA_API_BASE="http://192.168.1.10:11434"

# Color codes for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Models to check and pull if needed
MODELS=(
    # For coding tasks
    "qwen3:14b-instruct-q4_K_M"      # Newer Qwen3 model for coding
    "qwen2.5-coder:32b-instruct-q8_0" # Specialized coding model
    
    # For reasoning tasks
    "mixtral:8x22b-instruct-v0.1-q4_K_M" # Powerful reasoning model
    
    # For creative tasks
    "llama3:8b"                      # Good for creative tasks
    "qwen3:8b-instruct-q4_K_M"       # Newer alternative for creative tasks
    
    # For general chat
    "qwen3:32b-instruct-q4_K_M"      # Latest Qwen3 model
    "qwen2.5:32b-instruct-q4_K_M"    # Current default model
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

echo -e "\n${BLUE}Checking for required models...${NC}"
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
    echo -e "\n${GREEN}All required models are already installed!${NC}"
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

echo -e "\n${GREEN}Done!${NC}"
