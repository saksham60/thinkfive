import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import '../../domain/repositories/dashboard_repository.dart';
import '../../domain/entities/customer_dashboard.dart';

abstract class DashboardEvent extends Equatable {
  @override
  List<Object?> get props => [];
}
class LoadDashboard extends DashboardEvent {}

abstract class DashboardState extends Equatable {
  @override
  List<Object?> get props => [];
}
class DashboardInitial extends DashboardState {}
class DashboardLoading extends DashboardState {}
class DashboardLoaded extends DashboardState {
  final CustomerDashboardEntity dashboard;
  DashboardLoaded(this.dashboard);
  @override
  List<Object?> get props => [dashboard];
}
class DashboardError extends DashboardState {
  final String message;
  DashboardError(this.message);
  @override
  List<Object?> get props => [message];
}

class DashboardBloc extends Bloc<DashboardEvent, DashboardState> {
  final DashboardRepository repository;

  DashboardBloc(this.repository) : super(DashboardInitial()) {
    on<LoadDashboard>((event, emit) async {
      emit(DashboardLoading());
      try {
        final data = await repository.getCustomerDashboard();
        emit(DashboardLoaded(data));
      } catch (e) {
        emit(DashboardError(e.toString()));
      }
    });
  }
}
