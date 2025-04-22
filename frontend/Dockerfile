FROM node:18-alpine
# Install dependencies and build the application
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . . 
ARG BACKEND_URL
# Set the backend URL for the frontend application
ENV VITE_API_URL=${BACKEND_URL}
#RUN npm run build

EXPOSE 5173

CMD ["npm", "run", "dev"]

# # Use nginx to serve the built application
# FROM nginx:alpine
# COPY --from=0 /app/dist /usr/share/nginx/html
# EXPOSE 80
# CMD ["nginx", "-g", "daemon off;"]
