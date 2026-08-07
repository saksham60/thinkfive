import '../../domain/entities/user.dart';
import '../../domain/repositories/auth_repository.dart';

class FixtureAuthRepository implements AuthRepository {
  User? _currentUser;
  
  @override
  Future<User> login(String email, String password) async {
    await Future.delayed(const Duration(seconds: 1));
    
    if (email.contains('analyst')) {
      _currentUser = const User(userId: 'u_analyst1', email: 'analyst@thinkfive.com', role: AppRole.analyst);
    } else if (email.contains('supervisor')) {
      _currentUser = const User(userId: 'u_supervisor1', email: 'supervisor@thinkfive.com', role: AppRole.supervisor);
    } else if (email.contains('admin')) {
      _currentUser = const User(userId: 'u_admin1', email: 'admin@thinkfive.com', role: AppRole.admin);
    } else {
      _currentUser = const User(userId: 'u_customer1', email: 'priya@thinkfive.com', role: AppRole.customer, customerId: 'c_12345');
    }
    
    return _currentUser!;
  }

  @override
  Future<void> logout() async {
    await Future.delayed(const Duration(milliseconds: 500));
    _currentUser = null;
  }

  @override
  Future<User?> checkSession() async {
    await Future.delayed(const Duration(milliseconds: 500));
    return _currentUser;
  }
}
