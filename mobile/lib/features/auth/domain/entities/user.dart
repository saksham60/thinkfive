import 'package:equatable/equatable.dart';

enum AppRole { customer, analyst, supervisor, admin }

class User extends Equatable {
  final String userId;
  final String email;
  final AppRole role;
  final String? customerId;

  const User({
    required this.userId,
    required this.email,
    required this.role,
    this.customerId,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    AppRole parsedRole;
    switch (json['role']?.toString().toUpperCase()) {
      case 'ANALYST':
        parsedRole = AppRole.analyst;
        break;
      case 'SUPERVISOR':
        parsedRole = AppRole.supervisor;
        break;
      case 'ADMIN':
        parsedRole = AppRole.admin;
        break;
      case 'CUSTOMER':
      default:
        parsedRole = AppRole.customer;
    }

    return User(
      userId: json['user_id'] as String? ?? json['id'] as String? ?? '',
      email: json['email'] as String? ?? '',
      role: parsedRole,
      customerId: json['customer_id'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'user_id': userId,
      'email': email,
      'role': role.name.toUpperCase(),
      'customer_id': customerId,
    };
  }

  @override
  List<Object?> get props => [userId, email, role, customerId];
}
