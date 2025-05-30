# 🍽️ Food Delivery Microservices Backend

This project implements a simplified food delivery backend system using a microservices architecture. It demonstrates inter-service communication, database persistence with PostgreSQL, and a GraphQL API gateway for client interaction.

---

## 🚀 Architecture Overview

The system is composed of four main services, orchestrated using Docker Compose:

* **postgres\_db**: The central database for `restaurant_service` and `delivery_agent_service`.
* **restaurant\_service**: Manages restaurants, their menus, and the lifecycle of food orders. It interacts with `delivery_agent_service` for agent assignment.
* **delivery\_agent\_service**: Manages delivery agents, their availability, and handles the assignment and completion of deliveries.
* **user\_service (GraphQL Gateway)**: Acts as the primary API gateway for client applications. It exposes a GraphQL endpoint and aggregates calls to the underlying services.

---

## 🛠️ Technologies Used

* **Backend Framework**: FastAPI (Python)
* **ORM**: Tortoise ORM (Async ORM)
* **Database**: PostgreSQL
* **Inter-service Communication**: httpx
* **GraphQL**: Strawberry
* **Containerization**: Docker & Docker Compose
* **Python**: 3.10+

---

## ✨ Key Features

* Microservices Architecture
* Asynchronous Operations
* PostgreSQL-backed Persistence
* GraphQL API Gateway
* Full Order Lifecycle Management
* Dynamic Menu and Agent Management
* Automated Agent Assignment
* Order Rating
* Dockerized Deployment

---

## 🚀 Setup & Installation

### Prerequisites

* Git
* Docker & Docker Compose

### 1. Clone the Repository

```bash
git clone  https://github.com/spidyshivam/kraftbase-assignment
cd kraftbase-assignment
```
### 2. Run with Docker Compose

```bash
docker-compose down --volumes --rmi all
docker-compose up --build -d
```

### 3. Verify Running Services

```bash
docker-compose ps
```

All services should show `Up`.

---

## 🦖 API Endpoints & Testing

### Ports

* **GraphQL**: [http://localhost:8000/graphql](http://localhost:8000/graphql)
* **Restaurant REST**: [http://localhost:8001](http://localhost:8001)
* **Delivery Agent REST**: [http://localhost:8002](http://localhost:8002)

### Initial Data Setup

#### 1. Add Restaurant

```bash
curl -X POST http://localhost:8001/restaurants \
-H "Content-Type: application/json" \
-d '{"name": "The Burger Joint", "online": true}'
```

#### 2. Add Menu Item

```bash
curl -X POST http://localhost:8001/restaurants/1/menu \
-H "Content-Type: application/json" \
-d '{"name": "Classic Burger", "description": "Beef patty with cheese", "price": 10.50, "available": true}'
```

#### 3. Add Delivery Agent

```bash
curl -X POST http://localhost:8002/agents \
-H "Content-Type: application/json" \
-d '{"name": "Agent Speedy", "available": true}'
```

---

## 🔢 GraphQL

### 1. Mutation: Place Order

```graphql
mutation PlaceNewOrder {
  placeOrder(orderData: {
    userId: 101,
    restaurantId: 1,
    items: ["Classic Burger", "Fries", "Coke"]
  }) {
    id
    userId
    restaurantId
    status
    items
    restaurant {
      name
    }
    assignedAgent {
      name
    }
  }
}
```

### 2. Accept Order

```bash
curl -X PUT http://localhost:8001/orders/1/status \
-H "Content-Type: application/json" \
-d '{"status": "accepted"}'
```

### 3. Query: Order Details

```graphql
query GetFullOrderDetails {
  getOrder(orderId: 1) {
    id
    status
    items
    restaurant {
      id
      name
      online
      menu {
        name
        price
      }
    }
    assignedAgent {
      id
      name
      available
    }
  }
}
```

### 4. Complete Delivery

```bash
curl -X POST http://localhost:8002/complete-delivery \
-H "Content-Type: application/json" \
-d '{"order_id": 1, "agent_id": 1}'
```

### 5. Rate Order

```graphql
mutation SubmitOrderRating {
  rateOrder(orderId: 1, restaurantRating: 5, agentRating: 4)
}
```

---

## 🚼 Cleaning Up

```bash
docker-compose down --volumes
```



---
