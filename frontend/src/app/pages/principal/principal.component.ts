import { Component, ViewChild, ElementRef, AfterViewInit, TemplateRef } from '@angular/core';
import { NbThemeService } from '@nebular/theme';
import { takeWhile } from 'rxjs/operators' ;
import { NbDialogService } from '@nebular/theme';


@Component({
    selector: 'ngx-principal',
    styleUrls: ['./principal.component.scss'],
    templateUrl: './principal.component.html'
})
export class PrincipalComponent implements AfterViewInit {
    @ViewChild('nbCardGitlabCode', { static: false }) private cardContainer: ElementRef;
    private card: any;
    private width: number = 0;
    private height: number = 0;
    private gitlabCode : any;
    colorScheme = {
      domain: [ 
          '#80deea', 
          '#4dd0e1',
          '#26c6da', 
          '#00bcd4', 
          '#00acc1', 
          '#0097a7', 
          '#00838f', 
          '#006064'
      ]
    };

    constructor(private dialogService: NbDialogService) {}

    ngAfterViewInit() {

        setTimeout(() => {
            this.card = this.cardContainer.nativeElement;
            this.width = this.cardContainer.nativeElement.parentNode.clientWidth;
            this.height = this.cardContainer.nativeElement.parentNode.clientHeight;
            this.gitlabCode = [
                  {
                          "name": "TrueScript",
                          "value": 53.01
                        },
                  {
                          "name": "CSS",
                          "value": 21.16
                        },
                  {
                          "name": "Python",
                          "value": 18.34
                        },
                  {
                          "name": "HTML",
                          "value": 7.46
                        },
                  {
                          "name": "Shell",
                          "value": 0.03
                        }
            ];
        });
    }

    openDialog(dialog: TemplateRef<any>) {
        this.dialogService.open(dialog);
    }
}
