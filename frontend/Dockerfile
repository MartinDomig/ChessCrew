# Use official Node.js LTS image
FROM node:20-alpine

# Install git for cache versioning
RUN apk add --no-cache git

# Configure git to allow access to workspace directory
RUN git config --global --add safe.directory /workspace

WORKDIR /app

# Expose default React port
EXPOSE 3000

# Start React development server
CMD ["npm", "start"]
