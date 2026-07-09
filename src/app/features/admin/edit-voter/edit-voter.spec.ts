import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { of } from 'rxjs';

import { ApiService } from '../../../core/services/api';
import { EditVoterComponent } from './edit-voter';

describe('EditVoterComponent', () => {
  let component: EditVoterComponent;
  let fixture: ComponentFixture<EditVoterComponent>;
  let apiService: jasmine.SpyObj<ApiService>;

  beforeEach(async () => {
    apiService = jasmine.createSpyObj('ApiService', ['getVoter']);
    apiService.getVoter.and.returnValue(of({
      voter_id: 'V777',
      name: 'Real Voter',
      email: 'real-voter@example.com'
    }));

    await TestBed.configureTestingModule({
      imports: [EditVoterComponent, RouterTestingModule],
      providers: [
        { provide: ApiService, useValue: apiService },
        { provide: ActivatedRoute, useValue: { paramMap: of({ get: () => '7' }) } }
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(EditVoterComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load the real voter email from the API', () => {
    expect(apiService.getVoter).toHaveBeenCalledWith(7);
    expect(component.editVoterForm.get('email')?.value).toBe('real-voter@example.com');
  });
});
