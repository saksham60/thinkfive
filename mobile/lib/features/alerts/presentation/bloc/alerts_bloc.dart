import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import '../../domain/repositories/alert_repository.dart';
import '../../domain/entities/fraud_alert.dart';

abstract class AlertsEvent extends Equatable {
  const AlertsEvent();
  @override
  List<Object?> get props => [];
}

class LoadAlerts extends AlertsEvent {}

class LoadAlertDetail extends AlertsEvent {
  final String alertId;
  const LoadAlertDetail(this.alertId);
  @override
  List<Object?> get props => [alertId];
}

class AlertsState extends Equatable {
  final List<FraudAlertEntity> alerts;
  final FraudAlertEntity? selectedAlert;
  final bool isLoading;
  final String? error;

  const AlertsState({
    this.alerts = const [],
    this.selectedAlert,
    this.isLoading = false,
    this.error,
  });

  AlertsState copyWith({
    List<FraudAlertEntity>? alerts,
    FraudAlertEntity? selectedAlert,
    bool? isLoading,
    String? error,
    bool clearSelected = false,
    bool clearError = false,
  }) {
    return AlertsState(
      alerts: alerts ?? this.alerts,
      selectedAlert: clearSelected
          ? null
          : (selectedAlert ?? this.selectedAlert),
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
    );
  }

  @override
  List<Object?> get props => [alerts, selectedAlert, isLoading, error];
}

class AlertsBloc extends Bloc<AlertsEvent, AlertsState> {
  final AlertRepository _repository;

  AlertsBloc(this._repository) : super(const AlertsState()) {
    on<LoadAlerts>(_onLoadAlerts);
    on<LoadAlertDetail>(_onLoadAlertDetail);
  }

  Future<void> _onLoadAlerts(
    LoadAlerts event,
    Emitter<AlertsState> emit,
  ) async {
    emit(state.copyWith(isLoading: true, clearError: true));
    try {
      final alerts = await _repository.getAlerts();
      emit(state.copyWith(alerts: alerts, isLoading: false));
    } catch (e) {
      emit(state.copyWith(isLoading: false, error: e.toString()));
    }
  }

  Future<void> _onLoadAlertDetail(
    LoadAlertDetail event,
    Emitter<AlertsState> emit,
  ) async {
    emit(
      state.copyWith(isLoading: true, clearError: true, clearSelected: true),
    );
    try {
      final alert = await _repository.getAlertDetail(event.alertId);
      emit(state.copyWith(selectedAlert: alert, isLoading: false));
    } catch (e) {
      emit(state.copyWith(isLoading: false, error: e.toString()));
    }
  }
}
