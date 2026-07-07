import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';

import { EditVoterComponent } from './edit-voter';

describe('EditVoterComponent', () => {
  let component: EditVoterComponent;
  let fixture: ComponentFixture<EditVoterComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [EditVoterComponent, RouterTestingModule],
    }).compileComponents();

    fixture = TestBed.createComponent(EditVoterComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
