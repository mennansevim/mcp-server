# .NET Fundamentals Rules

## C# Language Features

### Nullable Reference Types
✅ **Use nullable annotations properly**
```csharp
// Good
string? nullableName = GetName(); // May be null
string definiteName = GetName() ?? "default"; // Never null

// Bad
string name = GetName(); // Compiler warning if GetName() returns string?
```

### Async/Await
✅ **Proper async patterns**
```csharp
// Good
public async Task<User> GetUserAsync(int id)
{
    return await _db.Users.FindAsync(id);
}

// Bad
public Task<User> GetUserAsync(int id)
{
    return Task.Run(() => _db.Users.Find(id)); // Don't use Task.Run in libraries
}
```

❌ **Avoid async void** (except event handlers)
```csharp
// Bad
public async void ProcessData() { } // Exceptions can't be caught!

// Good
public async Task ProcessDataAsync() { }
```

### LINQ Best Practices
⚠️ **Avoid multiple enumeration**
```csharp
// Bad
var items = GetItems().Where(x => x.IsActive);
var count = items.Count(); // Enumerates
var first = items.First();  // Enumerates again!

// Good
var items = GetItems().Where(x => x.IsActive).ToList();
var count = items.Count;
var first = items.First();
```

---

## ASP.NET Core

### Dependency Injection
✅ **Proper service registration**
```csharp
// Correct lifetimes
services.AddSingleton<ICache, MemoryCache>();     // Shared instance
services.AddScoped<IDbContext, AppDbContext>();   // Per request
services.AddTransient<IEmailService, EmailService>(); // Per resolution

// Bad: DbContext as Singleton (thread-unsafe!)
services.AddSingleton<AppDbContext>(); 
```

### Controller Best Practices
✅ **Use async actions**
```csharp
// Good
[HttpGet("{id}")]
public async Task<ActionResult<User>> GetUser(int id)
{
    var user = await _userService.GetAsync(id);
    return user == null ? NotFound() : Ok(user);
}
```

❌ **Don't use [FromBody] for GET**
```csharp
// Bad
[HttpGet]
public IActionResult Get([FromBody] SearchCriteria criteria) // GET shouldn't have body
```

### Model Validation
✅ **Always validate models**
```csharp
[HttpPost]
public async Task<IActionResult> Create([FromBody] CreateUserDto dto)
{
    if (!ModelState.IsValid)
        return BadRequest(ModelState);
    
    // Process...
}
```

---

## Entity Framework Core

### Query Performance
❌ **Avoid N+1 queries**
```csharp
// Bad
var users = await _db.Users.ToListAsync();
foreach (var user in users)
{
    var orders = await _db.Orders.Where(o => o.UserId == user.Id).ToListAsync(); // N+1!
}

// Good
var users = await _db.Users
    .Include(u => u.Orders)
    .ToListAsync();
```

### Change Tracking
⚠️ **Use AsNoTracking for read-only queries**
```csharp
// Read-only operation
var users = await _db.Users
    .AsNoTracking()
    .ToListAsync();
```

### Transactions
✅ **Use transactions for multiple operations**
```csharp
using var transaction = await _db.Database.BeginTransactionAsync();
try
{
    _db.Users.Add(user);
    await _db.SaveChangesAsync();
    
    _db.Orders.Add(order);
    await _db.SaveChangesAsync();
    
    await transaction.CommitAsync();
}
catch
{
    await transaction.RollbackAsync();
    throw;
}
```

---

## Exception Handling

### Proper Patterns
✅ **Catch specific exceptions**
```csharp
// Good
try
{
    await ProcessAsync();
}
catch (DbUpdateException ex)
{
    _logger.LogError(ex, "Database update failed");
    throw new ApplicationException("Failed to save data", ex);
}

// Bad
catch (Exception ex) // Too broad
{
    return null; // Swallowing exception
}
```

❌ **Don't catch and rethrow without adding value**
```csharp
// Bad
try { }
catch (Exception ex)
{
    throw ex; // Loses stack trace! Use 'throw;' instead
}
```

---

## Configuration

### appsettings.json
✅ **Use strongly-typed configuration**
```csharp
// Good
public class EmailSettings
{
    public string SmtpServer { get; set; }
    public int Port { get; set; }
}

services.Configure<EmailSettings>(Configuration.GetSection("Email"));
```

❌ **Don't store secrets in appsettings.json**
```json
{
  "ConnectionStrings": {
    "Default": "Server=prod;Password=secret123" // BAD!
  }
}
```

---

## Memory Management

### IDisposable
✅ **Always dispose IDisposable resources**
```csharp
// Good
using var connection = new SqlConnection(connectionString);
// or
using (var connection = new SqlConnection(connectionString))
{
    // Use connection
}

// Bad
var connection = new SqlConnection(connectionString);
// Forgot to dispose!
```

### Avoid Memory Leaks
❌ **Unsubscribe event handlers**
```csharp
// Bad
public class Subscriber
{
    public Subscriber(Publisher publisher)
    {
        publisher.Event += Handler; // Memory leak if not unsubscribed!
    }
}

// Good
public class Subscriber : IDisposable
{
    private Publisher _publisher;
    
    public Subscriber(Publisher publisher)
    {
        _publisher = publisher;
        _publisher.Event += Handler;
    }
    
    public void Dispose()
    {
        _publisher.Event -= Handler;
    }
}
```

---

## Common Mistakes

### String Concatenation in Loops
❌ **Use StringBuilder**
```csharp
// Bad
string result = "";
for (int i = 0; i < 1000; i++)
{
    result += i.ToString(); // Creates 1000 string objects!
}

// Good
var sb = new StringBuilder();
for (int i = 0; i < 1000; i++)
{
    sb.Append(i);
}
string result = sb.ToString();
```

### Blocking Async Code
❌ **Never use .Result or .Wait()**
```csharp
// Bad
var user = GetUserAsync().Result; // Can cause deadlocks!

// Good
var user = await GetUserAsync();
```

### Improper Task Usage
❌ **Don't use Task.Run in libraries**
```csharp
// Bad (in library code)
public Task<Data> GetDataAsync()
{
    return Task.Run(() => LoadData());
}

// Good
public async Task<Data> GetDataAsync()
{
    return await LoadDataAsync();
}
```

---

## Checklist

- [ ] Nullable reference types used correctly
- [ ] Async/await used properly (no .Result/.Wait)
- [ ] DI lifetimes appropriate (Singleton/Scoped/Transient)
- [ ] EF queries optimized (no N+1, use AsNoTracking)
- [ ] IDisposable resources properly disposed
- [ ] Exceptions caught at appropriate level
- [ ] Configuration uses strongly-typed options
- [ ] No secrets in appsettings.json
- [ ] Event handlers unsubscribed
- [ ] StringBuilder used for string concatenation in loops

