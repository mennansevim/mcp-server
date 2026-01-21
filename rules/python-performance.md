# Performance Rules
## Database Performance

### N+1 Query Problem
❌ **CRITICAL PERFORMANCE ISSUE**
```python
# Bad: N+1 queries (1 query + N queries for each item)
users = User.query.all()  # 1 query
for user in users:
    user.orders = Order.query.filter_by(user_id=user.id).all()  # N queries!

# Good: Single query with join
users = User.query.join(Order).all()  # 1 query!
```

### Query Optimization
✅ **Select only needed columns**
```python
# Bad: Loads entire entity
users = User.query.all()

# Good: Select only needed data
users = User.query.with_entities(User.id, User.name).all()
```

### Indexing
⚠️ **Ensure proper indexes**
```python
# If querying by Email frequently:
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String, index=True)

# If querying by multiple columns:
class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    created_date = Column(DateTime, index=True)
```

---

## Caching

### Expensive Operations
✅ **Cache frequently accessed data**
```python
# Good: Cache expensive operations
from functools import lru_cache

@lru_cache(maxsize=128)
def get_categories():
    return Category.query.all()
```

### Cache Invalidation
⚠️ **Don't forget to invalidate**
```python
def update_category(category):
    db.session.commit()
    # Invalidate cache
    get_categories.cache_clear()
```

---

## Memory Efficiency

### Large Collections
❌ **Avoid loading entire collections**
```python
# Bad: Loads everything into memory
all_users = User.query.all()  # Could be millions!
active_users = [user for user in all_users if user.is_active]

# Good: Filter in database
active_users = User.query.filter_by(is_active=True).all()
```

### Streaming Large Data
✅ **Use generators for large datasets**
```python
# Good: Streams data without loading all into memory
def get_users_stream():
    for user in User.query.yield_per(100):
        yield user
```

### String Operations
❌ **Use join() for concatenation**
```python
# Bad: Creates many string objects
result = ""
for i in range(10000):
    result += str(i)

# Good: Single allocation
result = "".join(map(str, range(10000)))
```

---

## Async Operations

### Parallel Execution
✅ **Use asyncio.gather for independent operations**
```python
# Bad: Sequential (slow)
users = await get_users()
orders = await get_orders()
products = await get_products()

# Good: Parallel (fast)
users_task = asyncio.create_task(get_users())
orders_task = asyncio.create_task(get_orders())
products_task = asyncio.create_task(get_products())

await asyncio.gather(users_task, orders_task, products_task)

users = users_task.result()
orders = orders_task.result()
products = products_task.result()
```

### ConfigureAwait
✅ **Use asyncio.run() in main**
```python
# In main
async def main():
    # ...

asyncio.run(main())
```

---

## API Performance

### Pagination
❌ **Never return all records without pagination**
```python
# Bad: Could return millions of records
@app.route("/items")
def get_items():
    items = Item.query.all()
    return jsonify([item.to_dict() for item in items])

# Good: Paginated
@app.route("/items")
def get_items(page=1, per_page=20):
    items = Item.query.paginate(page, per_page, False)
    return jsonify([item.to_dict() for item in items.items])
```

### Response Compression
✅ **Enable compression for large responses**
```python
from flask import Flask, jsonify
from flask_compress import Compress

app = Flask(__name__)
Compress(app)
```

### ETag / Caching Headers
✅ **Use HTTP caching**
```python
from flask import make_response

@app.route("/item/<int:item_id>")
def get_item(item_id):
    item = Item.query.get(item_id)
    response = make_response(jsonify(item.to_dict()))
    response.headers["Cache-Control"] = "max-age=60"
    return response
```

---

## LINQ Performance

### Deferred Execution
⚠️ **Be aware of multiple enumerations**
```python
# Bad: Query executed twice
users = User.query.filter_by(is_active=True)
count = users.count()   # Executes query
items = users.all()  # Executes again!

# Good: Execute once
users = User.query.filter_by(is_active=True).all()
count = len(users)
```

### Any() vs Count()
✅ **Use any() for existence checks**
```python
# Bad: Counts all items
if User.query.filter_by(is_active=True).count() > 0:

# Good: Stops at first item
if User.query.filter_by(is_active=True).first() is not None:
```

### First() vs FirstOrDefault()
✅ **Choose appropriate method**
```python
# Bad: Exception if not found
user = User.query.first()  # Raises if empty

# Good: Returns None if not found
user = User.query.first()
if user is None:
    return jsonify({"error": "not found"}), 404
```

---

## JSON Serialization

### Ignore Cycles
```python
from flask import jsonify

@app.route("/item/<int:item_id>")
def get_item(item_id):
    item = Item.query.get(item_id)
    return jsonify(item.to_dict())
```

### Selective Serialization
✅ **Use DTOs to control output**
```python
# Bad: Returns entire entity graph
return jsonify(item.to_dict())  # Includes orders, orders.items, etc.

# Good: Return only needed data
return jsonify({"id": item.id, "name": item.name, "order_count": len(item.orders)})
```

---

## Common Performance Antipatterns

### Over-fetching
```python
# Bad: Loads entire entity when only ID needed
user_id = user.manager.department.company.owner_id

# Good: Specific query
user_id = User.query.with_entities(User.id).filter_by(id=user.id).first()
```

### Premature Materialization
```python
# Bad: ToList() before filtering
users = User.query.all()  # Loads ALL users into memory
active_users = [user for user in users if user.is_active]

# Good: Filter in database
active_users = User.query.filter_by(is_active=True).all()
```

---

## Monitoring & Profiling

### Logging Slow Queries
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("postgresql://user:password@host:port/dbname")
Session = sessionmaker(bind=engine)

session = Session()
session.execute("SET statement_timeout = 1000")  # 1 second
```

---

## Checklist

- [ ] No N+1 query problems
- [ ] Appropriate indexes on database columns
- [ ] Caching implemented for expensive operations
- [ ] Pagination implemented for large datasets
- [ ] join() used for string concatenation
- [ ] asyncio.gather used for independent tasks
- [ ] Response compression enabled
- [ ] HTTP caching headers used
- [ ] LINQ queries not executed multiple times
- [ ] any() used instead of count() > 0
- [ ] DTOs used to control serialization
- [ ] yield_per used for read-only queries
- [ ] Large data streamed instead of loaded entirely

---

## Severity Guidelines

| Issue | Severity |
|-------|----------|
| N+1 queries | **HIGH** |
| Loading entire table without pagination | **HIGH** |
| Missing database indexes (frequent queries) | **MEDIUM** |
| Not using caching | **MEDIUM** |
| String concatenation in loops | **MEDIUM** |
| Multiple LINQ enumerations | **LOW** |
| Using count() instead of any() | **LOW** |