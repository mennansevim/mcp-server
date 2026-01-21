# Performance Rules
## Database Performance

### N+1 Query Problem
❌ **CRITICAL PERFORMANCE ISSUE**
```csharp
// Bad: N+1 queries (1 query + N queries for each item)
var users = await _db.Users.ToListAsync(); // 1 query
foreach (var user in users)
{
    user.Orders = await _db.Orders
        .Where(o => o.UserId == user.Id)
        .ToListAsync(); // N queries!
}

// Good: Single query with Include
var users = await _db.Users
    .Include(u => u.Orders)
    .ToListAsync(); // 1 query!
```

### Query Optimization
✅ **Select only needed columns**
```csharp
// Bad: Loads entire entity
var users = await _db.Users
    .Where(u => u.IsActive)
    .ToListAsync();

// Good: Select only needed data
var users = await _db.Users
    .Where(u => u.IsActive)
    .Select(u => new { u.Id, u.Name })
    .ToListAsync();
```

### Indexing
⚠️ **Ensure proper indexes**
```csharp
// If querying by Email frequently:
modelBuilder.Entity<User>()
    .HasIndex(u => u.Email);
    
// If querying by multiple columns:
modelBuilder.Entity<Order>()
    .HasIndex(o => new { o.UserId, o.CreatedDate });
```

## Caching

### Expensive Operations
✅ **Cache frequently accessed data**
```csharp
// Good: Cache expensive operations
public async Task<List<Category>> GetCategoriesAsync()
{
    return await _cache.GetOrCreateAsync("categories", async entry =>
    {
        entry.AbsoluteExpirationRelativeToNow = TimeSpan.FromHours(1);
        return await _db.Categories.ToListAsync();
    });
}
```

### Cache Invalidation
⚠️ **Don't forget to invalidate**
```csharp
public async Task UpdateCategoryAsync(Category category)
{
    await _db.SaveChangesAsync();
    _cache.Remove("categories"); // Invalidate cache
}
```

## Memory Efficiency

### Large Collections
❌ **Avoid loading entire collections**
```csharp
// Bad: Loads everything into memory
var allUsers = await _db.Users.ToListAsync(); // Could be millions!
var activeUsers = allUsers.Where(u => u.IsActive).ToList();

// Good: Filter in database
var activeUsers = await _db.Users
    .Where(u => u.IsActive)
    .ToListAsync();
```

### Streaming Large Data
✅ **Use IAsyncEnumerable for large datasets**
```csharp
// Good: Streams data without loading all into memory
public async IAsyncEnumerable<User> GetUsersStreamAsync()
{
    await foreach (var user in _db.Users.AsAsyncEnumerable())
    {
        yield return user;
    }
}
```

### String Operations
❌ **Use StringBuilder for concatenation**
```csharp
// Bad: Creates many string objects
string result = "";
for (int i = 0; i < 10000; i++)
{
    result += i.ToString();
}

// Good: Single allocation
var sb = new StringBuilder();
for (int i = 0; i < 10000; i++)
{
    sb.Append(i);
}
string result = sb.ToString();
```

## Async Operations

### Parallel Execution
✅ **Use Task.WhenAll for independent operations**
```csharp
// Bad: Sequential (slow)
var users = await GetUsersAsync();
var orders = await GetOrdersAsync();
var products = await GetProductsAsync();

// Good: Parallel (fast)
var usersTask = GetUsersAsync();
var ordersTask = GetOrdersAsync();
var productsTask = GetProductsAsync();

await Task.WhenAll(usersTask, ordersTask, productsTask);

var users = usersTask.Result;
var orders = ordersTask.Result;
var products = productsTask.Result;
```

### ConfigureAwait
✅ **Use ConfigureAwait(false) in libraries**
```csharp
// In library code (not UI)
public async Task<Data> GetDataAsync()
{
    var result = await _client.GetAsync(url)
        .ConfigureAwait(false); // Don't capture context
    return await result.Content.ReadAsAsync<Data>()
        .ConfigureAwait(false);
}
```

## API Performance

### Pagination
❌ **Never return all records without pagination**
```csharp
// Bad: Could return millions of records
[HttpGet]
public async Task<IActionResult> GetAll()
{
    var items = await _db.Items.ToListAsync();
    return Ok(items);
}

// Good: Paginated
[HttpGet]
public async Task<IActionResult> GetAll(
    [FromQuery] int page = 1,
    [FromQuery] int pageSize = 20)
{
    var items = await _db.Items
        .Skip((page - 1) * pageSize)
        .Take(pageSize)
        .ToListAsync();
    
    return Ok(items);
}
```

### Response Compression
✅ **Enable compression for large responses**
```csharp
services.AddResponseCompression(options =>
{
    options.EnableForHttps = true;
});
```

### ETag / Caching Headers
✅ **Use HTTP caching**
```csharp
[HttpGet("{id}")]
[ResponseCache(Duration = 60)] // Cache for 60 seconds
public async Task<IActionResult> Get(int id)
{
    var item = await _service.GetAsync(id);
    return Ok(item);
}
```

## LINQ Performance

### Deferred Execution
⚠️ **Be aware of multiple enumerations**
```csharp
// Bad: Query executed twice
var query = _db.Users.Where(u => u.IsActive);
var count = query.Count();   // Executes query
var items = query.ToList();  // Executes again!

// Good: Execute once
var items = await _db.Users
    .Where(u => u.IsActive)
    .ToListAsync();
var count = items.Count;
```

### Any() vs Count()
✅ **Use Any() for existence checks**
```csharp
// Bad: Counts all items
if (users.Count() > 0)

// Good: Stops at first item
if (users.Any())
```

### First() vs FirstOrDefault()
✅ **Choose appropriate method**
```csharp
// Bad: Exception if not found
var user = users.First(); // Throws if empty

// Good: Returns null if not found
var user = users.FirstOrDefault();
if (user == null) return NotFound();
```

## JSON Serialization

### Ignore Cycles
```csharp
services.AddControllers()
    .AddJsonOptions(options =>
    {
        options.JsonSerializerOptions.ReferenceHandler = 
            ReferenceHandler.IgnoreCycles;
    });
```

### Selective Serialization
✅ **Use DTOs to control output**
```csharp
// Bad: Returns entire entity graph
return Ok(user); // Includes Orders, Orders.Items, etc.

// Good: Return only needed data
return Ok(new UserDto
{
    Id = user.Id,
    Name = user.Name,
    OrderCount = user.Orders.Count
});
```

## Common Performance Antipatterns

### Over-fetching
```csharp
// Bad: Loads entire entity when only ID needed
var userId = user.Manager.Department.Company.OwnerId;

// Good: Specific query
var userId = await _db.Users
    .Where(u => u.Id == user.Id)
    .Select(u => u.Manager.Department.Company.OwnerId)
    .FirstAsync();
```

### Premature Materialization
```csharp
// Bad: ToList() before filtering
var activeUsers = _db.Users
    .ToList() // Loads ALL users into memory
    .Where(u => u.IsActive)
    .ToList();

// Good: Filter in database
var activeUsers = await _db.Users
    .Where(u => u.IsActive)
    .ToListAsync();
```

## Monitoring & Profiling

### Logging Slow Queries
```csharp
services.AddDbContext<AppDbContext>(options =>
{
    options.UseSqlServer(connectionString)
        .LogTo(Console.WriteLine, LogLevel.Information)
        .EnableSensitiveDataLogging()
        .EnableDetailedErrors();
});
```

## Checklist

- [ ] No N+1 query problems
- [ ] Appropriate indexes on database columns
- [ ] Caching implemented for expensive operations
- [ ] Pagination implemented for large datasets
- [ ] StringBuilder used for string concatenation
- [ ] Parallel execution used for independent tasks
- [ ] Response compression enabled
- [ ] HTTP caching headers used
- [ ] LINQ queries not executed multiple times
- [ ] Any() used instead of Count() > 0
- [ ] DTOs used to control serialization
- [ ] AsNoTracking used for read-only queries
- [ ] Large data streamed instead of loaded entirely

## Severity Guidelines

| Issue | Severity |
|-------|----------|
| N+1 queries | **HIGH** |
| Loading entire table without pagination | **HIGH** |
| Missing database indexes (frequent queries) | **MEDIUM** |
| Not using caching | **MEDIUM** |
| String concatenation in loops | **MEDIUM** |
| Multiple LINQ enumerations | **LOW** |
| Using Count() instead of Any() | **LOW** |