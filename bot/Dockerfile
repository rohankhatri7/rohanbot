FROM node:18-alpine

# Minimal production Dockerfile for the Discord bot
WORKDIR /app

# Install production dependencies only (faster, smaller image)
COPY package*.json ./
RUN npm ci --only=production || npm install --production

# Copy source
COPY . .

# Expose an optional port (bot doesn't require it, kept for debugging)
EXPOSE 3000

# Start bot
CMD ["node", "index.js"]
