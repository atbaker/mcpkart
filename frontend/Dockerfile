FROM node:22-slim

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy source
COPY . .

# Expose dev server port
EXPOSE 5173

# Run dev server (accessible from host)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
