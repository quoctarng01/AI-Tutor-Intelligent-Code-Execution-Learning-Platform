FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Production serve with nginx (optional) or dev server
EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
