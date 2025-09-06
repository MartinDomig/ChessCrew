# Use official Node.js LTS image
FROM node:20-alpine

# Install git for cache versioning
RUN apk add --no-cache git

# Configure git to allow access to workspace directory and handle ownership issues
RUN git config --global --add safe.directory /workspace && \
    git config --global --add safe.directory /app && \
    git config --global core.filemode false && \
    git config --global init.defaultBranch main

WORKDIR /app

# Expose default React port
EXPOSE 3000

# Start React development server
CMD ["npm", "start"]
