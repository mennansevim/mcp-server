# Best Practices Rules
## Code Quality

### Naming Conventions
✅ **Follow language conventions**
- Classes, Methods, Properties: `PascalCase`
- Local variables, parameters: `camelCase`
- Private fields: `_camelCase` or `camelCase`
- Constants: `UPPER_CASE` or `PascalCase`
- Interfaces: `IPascalCase`
- Enums: `PascalCase`

### Method Length
⚠️ **Methods should be focused and concise**
```csharp
// Bad: 200+ line method doing everything
public void CreateUser()
{
    // ...
}

// Good: Small, focused methods
public async Task<User> CreateUserAsync(CreateUserDto dto)
{
    ValidateUserData(dto);
    var user = MapToUser(dto);
    await SaveUserAsync(user);
    await SendWelcomeEmailAsync(user);
    return user;
}
```

### Single Responsibility Principle
✅ **Each class/method should have one reason to change**
```csharp
// Bad: UserService doing everything
public class UserService
{
    public void CreateUser() { }
    public void SendEmail() { }      // Should be EmailService
    public void ValidateAddress() { } // Should be AddressValidator
}

// Good: Separated concerns
public class UserService { /* User operations */ }
public class EmailService { /* Email operations */ }
public class AddressValidator { /* Address validation */ }
```

## SOLID Principles

### Dependency Inversion
✅ **Depend on abstractions, not concretions**
```csharp
// Bad: Depends on concrete class
public class OrderService
{
    private SqlOrderRepository _repo = new SqlOrderRepository();
}

// Good: Depends on interface
public class OrderService
{
    private readonly IOrderRepository _repo;
    
    public OrderService(IOrderRepository repo)
    {
        _repo = repo;
    }
}
```

### Interface Segregation
✅ **Interfaces should be client-specific**
```csharp
// Bad: Fat interface
public interface IUserService
{
    Task CreateAsync();
    Task UpdateAsync();
    Task DeleteAsync();
    Task SendEmailAsync();    // Not all clients need this
    Task ValidateAsync();     // Or this
}

// Good: Segregated interfaces
public interface IUserManager
{
    Task CreateAsync();
    Task UpdateAsync();
    Task DeleteAsync();
}

public interface IUserNotifier
{
    Task SendEmailAsync();
}
```

## Error Handling

### Meaningful Error Messages
✅ **Provide context in exceptions**
```csharp
// Bad
throw new Exception("Error");

// Good
throw new InvalidOperationException(
    $"Cannot process order {orderId} because it's already shipped. " +
    $"Status: {order.Status}, ShippedDate: {order.ShippedDate}"
);
```

### Don't Swallow Exceptions
❌ **Never catch and ignore**
```csharp
// Bad
try
{
    await ProcessAsync();
}
catch
{
    // Silent failure - debugging nightmare!
}

// Good
try
{
    await ProcessAsync();
}
catch (Exception ex)
{
    _logger.LogError(ex, "Failed to process data for user {UserId}", userId);
    throw; // Rethrow or handle appropriately
}
```

## Documentation

### XML Comments
✅ **Document public APIs**
```csharp
/// <summary>
/// Retrieves a user by their unique identifier.
/// </summary>
/// <param name="userId">The unique identifier of the user.</param>
/// <returns>The user if found; otherwise, null.</returns>
/// <exception cref="ArgumentException">Thrown when userId is less than 1.</exception>
public async Task<User?> GetUserAsync(int userId)
{
    if (userId < 1)
        throw new ArgumentException("User ID must be positive", nameof(userId));
    
    return await _db.Users.FindAsync(userId);
}
```

### README Files
✅ **Every project should have a README**
- Purpose of the project
- How to build/run
- Configuration requirements
- API documentation links

## Testing

### Unit Test Coverage
✅ **Aim for high coverage of business logic**
```csharp
[Fact]
public async Task CreateUser_WithValidData_CreatesUser()
{
    // Arrange
    var dto = new CreateUserDto { Name = "Test" };
    var service = new UserService(_mockRepo.Object);
    
    // Act
    var result = await service.CreateUserAsync(dto);
    
    // Assert
    Assert.NotNull(result);
    Assert.Equal("Test", result.Name);
    _mockRepo.Verify(r => r.AddAsync(It.IsAny<User>()), Times.Once);
}
```

### Test Naming
✅ **Use descriptive test names**
```csharp
// Good
[Fact]
public async Task GetUser_WhenUserDoesNotExist_ReturnsNotFound()

// Bad
[Fact]
public async Task Test1()
```

## Configuration

### Magic Numbers
❌ **Avoid magic numbers/strings**
```csharp
// Bad
if (user.Status == 2)
if (order.Type == "premium")

// Good
public enum UserStatus { Active = 1, Inactive = 2 }
public const string PremiumOrderType = "premium";

if (user.Status == UserStatus.Inactive)
if (order.Type == PremiumOrderType)
```

### Configuration Files
✅ **Use configuration, not hardcoded values**
```csharp
// Bad
var maxRetries = 3;
var timeout = 30;

// Good
var maxRetries = _configuration.GetValue<int>("Retry:MaxAttempts");
var timeout = _configuration.GetValue<int>("Http:TimeoutSeconds");
```

## Code Organization

### File Structure
✅ **Organize by feature, not by type**
```
// Bad
/Controllers
  UsersController.cs
  OrdersController.cs
/Services
  UserService.cs
  OrderService.cs
/Models
  User.cs
  Order.cs

// Good
/Features
  /Users
    UsersController.cs
    UserService.cs
    User.cs
    UserDto.cs
  /Orders
    OrdersController.cs
    OrderService.cs
    Order.cs
    OrderDto.cs
```

### Namespace Organization
✅ **Match folder structure**
```csharp
// File: Features/Users/UserService.cs
namespace MyApp.Features.Users
{
    public class UserService { }
}
```

## Security Best Practices

### Input Validation
✅ **Always validate inputs**
```csharp
public async Task<User> GetUserAsync(int userId)
{
    if (userId <= 0)
        throw new ArgumentException("Invalid user ID", nameof(userId));
    
    return await _db.Users.FindAsync(userId);
}
```

### Principle of Least Privilege
✅ **Grant minimum necessary permissions**
```csharp
// Database connection string
// Use read-only connection for queries
var readOnlyConnection = _configuration.GetConnectionString("ReadOnly");
```

## Performance Best Practices

### Lazy Loading vs Eager Loading
✅ **Choose appropriate loading strategy**
```csharp
// Eager loading when you know you'll need related data
var users = await _db.Users
    .Include(u => u.Orders)
    .ToListAsync();

// Explicit loading when conditional
if (needOrders)
{
    await _db.Entry(user)
        .Collection(u => u.Orders)
        .LoadAsync();
}
```

## Logging

### Structured Logging
✅ **Use structured logging with context**
```csharp
// Good
_logger.LogInformation(
    "User {UserId} created order {OrderId} for {Amount:C}",
    userId, orderId, amount
);

// Bad
_logger.LogInformation($"User {userId} created order {orderId} for {amount}");
```

### Log Levels
✅ **Use appropriate log levels**
- **Trace**: Very detailed (rarely used)
- **Debug**: Diagnostic information
- **Information**: General flow
- **Warning**: Unexpected but handled
- **Error**: Error that was caught
- **Critical**: Application crash

## API Design

### RESTful Conventions
✅ **Follow REST principles**
```csharp
// Good
GET    /api/users          // List users
GET    /api/users/{id}     // Get user
POST   /api/users          // Create user
PUT    /api/users/{id}     // Update user
DELETE /api/users/{id}     // Delete user

// Bad
POST /api/GetUser
POST /api/CreateUser
POST /api/UpdateUser
```

### Versioning
✅ **Version your APIs**
```csharp
[ApiController]
[Route("api/v1/[controller]")]
public class UsersController : ControllerBase
{
    // v1 implementation
}

[ApiController]
[Route("api/v2/[controller]")]
public class UsersController : ControllerBase
{
    // v2 implementation with breaking changes
}
```

## Severity Guidelines
| Rule | Severity |
| --- | --- |
| Naming Conventions | HIGH |
| Method Length | MEDIUM |
| Single Responsibility Principle | HIGH |
| Dependency Inversion | HIGH |
| Interface Segregation | HIGH |
| Error Handling | CRITICAL |
| Documentation | MEDIUM |
| Testing | HIGH |
| Configuration | MEDIUM |
| Code Organization | MEDIUM |
| Security Best Practices | CRITICAL |
| Performance Best Practices | MEDIUM |
| Logging | MEDIUM |
| API Design | HIGH |

## Checklist
- [ ] Naming conventions followed
- [ ] Methods are small and focused
- [ ] Single Responsibility Principle applied
- [ ] Dependency Inversion applied
- [ ] Interface Segregation applied
- [ ] Error handling implemented
- [ ] Documentation provided
- [ ] Tests written
- [ ] Configuration files used
- [ ] Code organized by feature
- [ ] Security best practices followed
- [ ] Performance best practices followed
- [ ] Logging implemented
- [ ] API design follows REST principles