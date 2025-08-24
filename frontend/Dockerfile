# Use official Node.js LTS image
FROM node:20-alpine

WORKDIR /app

# Copy package.json and package-lock.json if present
COPY package*.json ./

# Install dependencies (will fail if no package.json yet)
RUN npm install || true

# Copy rest of the app
COPY . .

# Expose default Vite port
EXPOSE 5173

# Start Vite dev server
CMD ["npm", "run", "dev", "--", "--host"]
