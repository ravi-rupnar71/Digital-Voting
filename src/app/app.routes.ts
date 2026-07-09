import { Routes } from '@angular/router';
import { VotingHomeComponent } from './features/public/home/home';
import { AdminLoginComponent } from './features/auth/admin-login/admin-login';
import { AdminOtpComponent } from './features/auth/admin-otp/admin-otp';
import { VerifyEmailComponent } from './features/auth/verify-email/verify-email';
import { VoterLoginComponent } from './features/auth/voter-login/voter-login';
import { VoterOtpComponent } from './features/auth/voter-otp/voter-otp';
import { AdminDashboardComponent } from './features/admin/dashboard/dashboard';
import { AddCandidateComponent } from './features/admin/add-candidate/add-candidate';
import { AddVoterComponent } from './features/admin/add-voter/add-voter';
import { EditCandidateComponent } from './features/admin/edit-candidate/edit-candidate';
import { EditVoterComponent } from './features/admin/edit-voter/edit-voter';
import { ResultsComponent } from './features/public/results/results';
import { VoteComponent as VotingPageComponent } from './features/voting/vote/vote';
import { VoteRecordedComponent } from './features/voting/already-voted/already-voted';
import { PageNotFoundComponent } from './features/public/page-not-found/page-not-found';

export const routes: Routes = [
  { path: '', component: VotingHomeComponent },
  { path: 'admin-login', component: AdminLoginComponent },
  { path: 'admin-otp', component: AdminOtpComponent },
  { path: 'verify-email', component: VerifyEmailComponent },
  { path: 'verify-email/:kind/:id', component: VerifyEmailComponent },
  { path: 'voter-login', component: VoterLoginComponent },
  { path: 'voter-otp', component: VoterOtpComponent },
  { path: 'vote', component: VotingPageComponent },
  { path: 'already-voted', component: VoteRecordedComponent },
  { path: 'results', component: ResultsComponent },
  { path: 'admin-dashboard', component: AdminDashboardComponent },
  { path: 'add-candidate', component: AddCandidateComponent },
  { path: 'add-voter', component: AddVoterComponent },
  { path: 'edit-candidate/:id', component: EditCandidateComponent },
  { path: 'edit-voter/:id', component: EditVoterComponent },
  { path: 'logout', redirectTo: '', pathMatch: 'full' },
  { path: '**', component: PageNotFoundComponent }
];
