import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import '../../domain/repositories/case_repository.dart';
import '../../domain/entities/case_entity.dart';

abstract class CasesEvent extends Equatable {
  const CasesEvent();
  @override
  List<Object?> get props => [];
}

class LoadCases extends CasesEvent {}

class LoadCaseDetail extends CasesEvent {
  final String caseId;
  const LoadCaseDetail(this.caseId);
  @override
  List<Object?> get props => [caseId];
}

class CasesState extends Equatable {
  final List<CaseEntity> cases;
  final CaseEntity? selectedCase;
  final bool isLoading;
  final String? error;

  const CasesState({
    this.cases = const [],
    this.selectedCase,
    this.isLoading = false,
    this.error,
  });

  CasesState copyWith({
    List<CaseEntity>? cases,
    CaseEntity? selectedCase,
    bool? isLoading,
    String? error,
    bool clearSelected = false,
    bool clearError = false,
  }) {
    return CasesState(
      cases: cases ?? this.cases,
      selectedCase: clearSelected ? null : (selectedCase ?? this.selectedCase),
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
    );
  }

  @override
  List<Object?> get props => [cases, selectedCase, isLoading, error];
}

class CasesBloc extends Bloc<CasesEvent, CasesState> {
  final CaseRepository _repository;

  CasesBloc(this._repository) : super(const CasesState()) {
    on<LoadCases>(_onLoadCases);
    on<LoadCaseDetail>(_onLoadCaseDetail);
  }

  Future<void> _onLoadCases(LoadCases event, Emitter<CasesState> emit) async {
    emit(state.copyWith(isLoading: true, clearError: true));
    try {
      final cases = await _repository.getCases();
      emit(state.copyWith(cases: cases, isLoading: false));
    } catch (e) {
      emit(state.copyWith(isLoading: false, error: e.toString()));
    }
  }

  Future<void> _onLoadCaseDetail(
    LoadCaseDetail event,
    Emitter<CasesState> emit,
  ) async {
    emit(
      state.copyWith(isLoading: true, clearError: true, clearSelected: true),
    );
    try {
      final caseEntity = await _repository.getCaseDetail(event.caseId);
      emit(state.copyWith(selectedCase: caseEntity, isLoading: false));
    } catch (e) {
      emit(state.copyWith(isLoading: false, error: e.toString()));
    }
  }
}
