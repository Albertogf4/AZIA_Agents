FROM node:20

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# 1) Genera la carpeta .next con la build
RUN npm run build

EXPOSE 3000

# 2) Ahora sí puedes arrancar la app de producción
CMD ["npm", "start"]
