import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';

import { EditCandidateComponent } from './edit-candidate';

describe('EditCandidateComponent', () => {
  let component: EditCandidateComponent;
  let fixture: ComponentFixture<EditCandidateComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [EditCandidateComponent, RouterTestingModule],
    }).compileComponents();

    fixture = TestBed.createComponent(EditCandidateComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
