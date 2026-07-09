import { ChangeDetectorRef, Component, OnInit, OnDestroy, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { ApiService } from '../../../core/services/api';

// Interfaces for strict typing
export interface Candidate {
  id: number;
  name: string;
  party: string;
  email: string;
  votes: number;
  is_verified: number;
}

export interface Voter {
  id: number;
  voter_id: string;
  name: string;
  email: string;
  has_voted: number;
  is_verified: number;
}

@Component({
  selector: 'app-admin-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './dashboard.html',
  styleUrls: ['./dashboard.css']
})
export class AdminDashboardComponent implements OnInit, OnDestroy {
  private readonly autoRefreshMs = 5000;
  private autoRefreshTimer: ReturnType<typeof setInterval> | null = null;

  messages: string[] = [];
  lastRefreshedAt: Date | null = null;
  
  candidates: Candidate[] = [];
  voters: Voter[] = [];

  // Modal State Variables
  isModalOpen = false;
  modalTitle = '';
  modalMessage = '';
  pendingAction: (() => void) | null = null;

  constructor(private api: ApiService, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    this.loadDashboard();
    this.startAutoRefresh();
  }

  ngOnDestroy(): void {
    this.stopAutoRefresh();
  }

  @HostListener('window:focus')
  onWindowFocus(): void {
    this.loadDashboard();
  }

  loadDashboard(): void {
    this.api.getAdminDashboard().subscribe({
      next: (data: any) => {
        this.candidates = data?.candidates || [];
        this.voters = data?.voters || [];
        this.lastRefreshedAt = new Date();
        this.cdr.markForCheck();
      },
      error: (err: any) => {
        const msg = err?.error?.error || 'Unable to load dashboard data.';
        this.messages = [msg];
        this.lastRefreshedAt = new Date();
        this.cdr.markForCheck();
      }
    });
  }

  refreshDashboard(): void {
    this.loadDashboard();
  }

  private startAutoRefresh(): void {
    this.stopAutoRefresh();
    this.autoRefreshTimer = setInterval(() => {
      this.loadDashboard();
    }, this.autoRefreshMs);
  }

  private stopAutoRefresh(): void {
    if (this.autoRefreshTimer) {
      clearInterval(this.autoRefreshTimer);
      this.autoRefreshTimer = null;
    }
  }

  // Dynamic getter replacing the Jinja2 |selectattr filter
  get votedCount(): number {
    return this.voters.filter(v => v.has_voted === 1).length;
  }

  // --- Modal Logic ---

  openModal(title: string, message: string, action: () => void): void {
    this.modalTitle = title;
    this.modalMessage = message;
    this.pendingAction = action;
    this.isModalOpen = true;
  }

  closeModal(): void {
    this.isModalOpen = false;
    this.pendingAction = null;
  }

  executeModalAction(): void {
    if (this.pendingAction) {
      this.pendingAction();
    }
    this.closeModal();
  }

  onBackdropClick(event: MouseEvent): void {
    this.closeModal();
  }

  // Listen for Escape key to close modal
  @HostListener('document:keydown.escape', ['$event'])
  onKeydownHandler(event: KeyboardEvent | Event) {
    if (this.isModalOpen) {
      this.closeModal();
    }
  }

  // --- Action Triggers ---

  confirmResetVotes(): void {
    this.openModal(
      'Reset vote totals',
      'This will clear all recorded votes and reset the voting counters. Continue?',
      () => {
        this.api.resetVotes().subscribe({
          next: () => {
            this.messages = ['All votes have been reset.'];
            this.loadDashboard();
          },
          error: (err: any) => {
            const msg = err?.error?.error || 'Unable to reset votes.';
            this.messages = [msg];
            this.cdr.markForCheck();
          }
        });
      }
    );
  }

  confirmDelete(id: number, type: 'voter' | 'candidate'): void {
    const message = type === 'voter'
      ? 'This voter will be removed from the system. Continue?'
      : 'This candidate will be removed from the system. Continue?';

    this.openModal(`Delete ${type}`, message, () => {
      const deleteRequest = type === 'voter'
        ? this.api.deleteVoter(id)
        : this.api.deleteCandidate(id);

      deleteRequest.subscribe({
        next: () => {
          if (type === 'voter') {
            this.voters = this.voters.filter(v => v.id !== id);
          } else {
            this.candidates = this.candidates.filter(c => c.id !== id);
          }
          this.messages = [`${type === 'voter' ? 'Voter' : 'Candidate'} deleted successfully.`];
          this.cdr.markForCheck();
        },
        error: (err: any) => {
          const msg = err?.error?.error || `Unable to delete ${type}. Please try again.`;
          this.messages = [msg];
          this.cdr.markForCheck();
        }
      });
    });
  }

  verifyCandidate(id: number): void {
    console.log(`Verify candidate ID: ${id}`);
    // Call API to verify candidate
  }

  verifyVoter(id: number): void {
    console.log(`Verify voter ID: ${id}`);
    // Call API to verify voter
  }
}
