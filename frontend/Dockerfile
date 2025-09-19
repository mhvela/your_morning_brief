FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* pnpm-lock.yaml* ./

RUN if [ -f pnpm-lock.yaml ]; then \
      npm i -g pnpm && pnpm install; \
    elif [ -f package-lock.json ]; then \
      npm ci; \
    else \
      npm i; \
    fi

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
