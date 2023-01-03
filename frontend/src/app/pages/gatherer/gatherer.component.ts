import { TemplateRef,
         ChangeDetectionStrategy,
         Component,
         OnInit,
         OnDestroy,
         ViewChild,
         ElementRef } from '@angular/core';

// import { NbThemeService } from '@nebular/theme';
import { DomSanitizer, SafeUrl } from '@angular/platform-browser';
import { NbDialogService } from '@nebular/theme';

// Search
import { NbSearchService } from '@nebular/theme';

// Data Service
import { DataGatherInfoService } from '../../@core/data/data-gather-info.service';

// Report
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import * as htmlToImage from 'html-to-image';
import { toPng, toJpeg, toBlob, toPixelData, toSvg } from 'html-to-image';

@Component({
    selector: 'ngx-gatherer',
    styleUrls: ['./gatherer.component.scss'],
    templateUrl: './gatherer.component.html',
    changeDetection: ChangeDetectionStrategy.Default
})

export class GathererComponent implements OnInit {
    @ViewChild('pageGather', { static: false }) private nbCardContainer: ElementRef;
    public  gathered: any = [];
    public  datas: any;
    public  processing: boolean = false;
    public  reportEnd: boolean = false;
    public  reportMessage: string;
    public  report: any;
    public  searchSubs: any;
    public  svg: any;
    public  img: any;
    public  divInvisible: any;
    public  getCanvas: any;
    public  downloadJsonHref: any;
    public  timeline: any = [];
    public  profile: any = [];

    // Report profile
    public  name: any = [];
    public  usern: any = [];
    public  location: any = [];
    public  url: any = [];
    public  bio: any = [];
    public  geo: any = [];
    public  gender: any = [];
    public  social: any = [];
    public  photo: any = [];
    public  organization: any = [];
    public  phone: any = [];
    public  emails: any = [];
    public  presence: any = [];

    public  onH: boolean = true;
    public  onS: boolean = true;
    public  onN: boolean = true;

    public  validationShow = {
        hard: true,
        soft: true,
        no: true,
    };

    public  flipped = false;


    constructor(private searchService: NbSearchService,
                private sanitizer: DomSanitizer,
                private dialogService: NbDialogService,
                private dataGatherService: DataGatherInfoService) {
    }

    ngOnInit() {
        this.searchSubs = this.searchService.onSearchSubmit()
          .subscribe((data: any) => {
            // Initialize global data
            this.gathered = this.dataGatherService.initialize();
            console.log('Global data initialize', this.gathered);

            console.log('Search', data);
            this.gathered = this.dataGatherService.validateEmail(data.term);
        });

        console.log('GathererComponent ngOnInit');
        // Check global data
        this.gathered = this.dataGatherService.pullGather();
        console.log('GathererComponent ngOnInit', this.gathered);
        console.log('GathererComponent ngOnInit length', this.jsonLength(this.gathered));
    }

    ngOnDestroy () {
        this.searchSubs.unsubscribe();
    }

    generateDownloadJsonUri() {
        let sJson = JSON.stringify(this.gathered);
        let element = document.createElement('a');
        element.setAttribute('href', 'data:text/json;charset=UTF-8,' + encodeURIComponent(sJson));
        element.setAttribute('download', 'gathered.json');
        element.style.display = 'none';
        document.body.appendChild(element);
        element.click(); // simulate click
        document.body.removeChild(element);
    }

    jsonLength(obj: any) {
        try {
          return Object.keys(obj).length;
        }
        catch(e) {
          return 0;
        }
    }

    setValidation(val: any) {
        this.validationShow[val] = !this.validationShow[val];
        console.log(this.validationShow);
    }

    checkValidation(val: any) {
        return this.validationShow[val]
    }

    toggleFlipViewAndSearch(email: string, username: string, 
                            twitter: string, instagram: string, 
                            linkedin: string, github: string, 
                            tiktok: string, tinder: string, 
                            venmo: string, reddit: string, 
                            spotify: string, twitch: string, 
                            keybase: string, mastodon: string) {
        console.log('Advance Search');
        console.log('email', email);
        console.log('username', username);
        console.log('twitter', twitter);
        console.log('instagram', instagram);
        console.log('linkedin', linkedin);
        console.log('github', github);
        console.log('tiktok', tiktok);
        console.log('tinder', tinder);
        console.log('venmo', venmo);
        console.log('reddit', reddit);
        console.log('spotify', spotify);
        console.log('twitch', twitch);
        console.log('keybase', keybase);
        console.log('mastodon', mastodon);

        this.flipped = !this.flipped;

        // JSON datas
        this.datas = {email: email,
            username: username,
            twitter: twitter,
            instagram: instagram,
            linkedin: linkedin,
            github: github,
            // tiktok: tiktok,
            // tinder: tinder,
            tiktok: '',
            tinder: '',
            venmo: venmo,
            reddit: reddit,
            spotify: spotify,
            twitch: twitch,
            keybase: keybase,
            mastodon: mastodon,
        };

        this.gathered = this.dataGatherService.initialize();
        console.log('Global data initialize (Advance Gatherer)', this.gathered);

        this.gathered = this.dataGatherService.gathererInfoAdvance(this.datas);
        this.gathered = this.dataGatherService.pullGather();

    }

    toggleFlipView() {
        this.flipped = !this.flipped;
    }

    // As All Functions in js are asynchronus, to use await i am using async here
    async generateAllPdfDialog(dialog: TemplateRef<any>) {
        this.reportEnd = false;
        this.dialogService.open(
          dialog,
          {
            context: 'this is some additional data passed to dialog',
            closeOnEsc: false,
            closeOnBackdropClick: false,
          });
        this.reportMessage = 'Initializing report...'

        console.log('Report... ');

        let infoText: string;
        let moduleHeight: number;
        this.profile = [];
        this.timeline = [];
        this.name = [];
        this.location = [];
        this.gender = [];
        this.organization = [];
        this.social = [];
        this.photo = [];

        // General config
        const doc = new jsPDF('p', 'mm', 'a4');
        const pageHeight = doc.internal.pageSize.getHeight();
        const img = new Image();
        const imgBack = new Image();
        const imgiKy = new Image();
        let hl = 0;
        let svg: any;

        // Config Page
        doc.internal.events.subscribe('addPage', function() {
            const pageSize = doc.internal.pageSize;
            // Side image
            doc.setDrawColor('#1a1a1a');
            doc.setFillColor('#1a1a1a');
            doc.rect(0, 0, pageSize.width, pageSize.height, 'F');
            doc.setDrawColor('#000000');
            doc.setFillColor('#000000');
            doc.rect(0, 0, 210, 15, 'F');
            doc.rect(0, 285, 210, 15, 'F');
            img.src = 'assets/images/back1.jpg';
            doc.addImage(img, 'png', 0, 15, 95, 270);

            // doc.addImage(myimage, 'JPG', 0, 0, pageSize.width, pageSize.height);
        });

        // Page 1
        doc.setDrawColor('#1a1a1a');
        doc.setFillColor('#1a1a1a');
        doc.rect(0, 0, 210, 300, 'F');
        imgBack.src = 'assets/images/blur-bg.jpg';
        doc.addImage(imgBack, 'png', 0, 50, 210, 200);

        img.src = 'assets/images/iKy-Logo.png';
        doc.addImage(img, 'png', 60, 105, 90, 98);

        // Top Line
        doc.setLineWidth(15);
        doc.setDrawColor('#000000');
        doc.line(10, 50, 200, 50);
        doc.line(10, 250, 200, 250);

        doc.setLineWidth(3);
        doc.setDrawColor('#05fcfc');
        doc.rect(50, 105, 110, 98, 'S');

        doc.setFont('helvetica');
        doc.setFontSize(50);
        doc.setTextColor('#05fcfc');
        doc.text('REPORT', 105, 100, {align: 'center'});

        /////////////////////////////////////////////////////////////////
        // Input page
        /////////////////////////////////////////////////////////////////
        doc.addPage();
        doc.setFontSize(25);
        hl = 20;

        // Header title page
        img.src = 'assets/images/h1.jpg';
        doc.addImage(img, 'png', 100, 15, 100, 14);
        img.src = 'assets/images/iKy-Logo.png';
        doc.addImage(img, 'png', 185, 17, 10, 10);
        doc.setFontSize(12);
        doc.setTextColor('#05fcfc');
        doc.text('INPUT - Selectors', 105, 23);

        // Header title page
        // img.src = 'assets/images/h2.png';
        // doc.addImage(img, 'png', 10, 10, 190, 14);
        // img.src = 'assets/images/iKy-Logo.png';
        // doc.addImage(img, 'png', 185, 12, 10, 10);
        // doc.setFontSize(12);
        // doc.setTextColor('#05fcfc');
        // doc.text('INPUT - Selectors', 15, 18);

        let email, username, twitter, instagram, linkedin, github, tiktok;
        let tinder, venmo, reddit, spotify, twitch;
        if (this.gathered['email'] && !this.gathered['data']) {
            email = this.gathered['email'];
        } else if (this.gathered['data'] && this.gathered['data']['email'] !== '') {
            email = this.gathered['data']['email'];
        } else {
            email = '-----';
        }
        username = (this.gathered['data'] && this.gathered['data']['username']) ?
            this.gathered['data']['username'] : '-----';
        twitter = (this.gathered['data'] && this.gathered['data']['twitter']) ?
            this.gathered['data']['twitter'] : '-----';
        instagram = (this.gathered['data'] && this.gathered['data']['instagram']) ?
            this.gathered['data']['instagram'] : '-----';
        linkedin = (this.gathered['data'] && this.gathered['data']['linkedin']) ?
            this.gathered['data']['linkedin'] : '-----';
        github = (this.gathered['data'] && this.gathered['data']['github']) ?
            this.gathered['data']['github'] : '-----';
        tiktok = (this.gathered['data'] && this.gathered['data']['tiktok']) ?
            this.gathered['data']['tiktok'] : '-----';
        tinder = (this.gathered['data'] && this.gathered['data']['tinder']) ?
            this.gathered['data']['tinder'] : '-----';
        venmo = (this.gathered['data'] && this.gathered['data']['venmo']) ?
            this.gathered['data']['venmo'] : '-----';
        reddit = (this.gathered['data'] && this.gathered['data']['reddit']) ?
            this.gathered['data']['reddit'] : '-----';
        spotify = (this.gathered['data'] && this.gathered['data']['spotify']) ?
            this.gathered['data']['spotify'] : '-----';
        twitch = (this.gathered['data'] && this.gathered['data']['twitch']) ?
            this.gathered['data']['twitch'] : '-----';

        const columns = [['Selectors', 'Values']];
        const rows = [
            ['E-mail', email],
            ['Username', username],
            ['Twitter', twitter],
            ['Instagram', instagram],
            ['Linkedin', linkedin],
            ['Github', github],
            ['Tiktok', tiktok],
            ['Tinder', tinder],
            ['Venmo', venmo],
            ['Reddit', reddit],
            ['Spotify', spotify],
            ['Twitch', twitch],
        ];

        autoTable(doc, {
             head: columns,
             body: rows,
             headStyles: {fillColor: '#50fcfc',
                          cellPadding: {top: 5, right: 5, bottom: 5, left: 5},
                          lineWidth: 3,
                          halign: 'center',
                          textColor: '#000000',
                          lineColor: '#1A1A1A'},
             bodyStyles: {fillColor: '#1A1A1A',
                          cellPadding: {top: 5, right: 5, bottom: 5, left: 5},
                          lineWidth: 3,
                          textColor: '#50fcfc',
                          lineColor: '#1A1A1A'},
             columnStyles: {
                 0: {fillColor: '#393f46', cellWidth: 50},
                 1: {fillColor: '#22262a', cellWidth: 70},
             },
             margin: {top: 60, left: 45},
        });

        /////////////////////////////////////////////////////////////////
        // TaskExec
        /////////////////////////////////////////////////////////////////
        doc.addPage();
        doc.setFontSize(25);

        // Header title page
        img.src = 'assets/images/h1.jpg';
        doc.addImage(img, 'png', 100, 15, 100, 14);
        img.src = 'assets/images/iKy-Logo.png';
        doc.addImage(img, 'png', 185, 17, 10, 10);
        doc.setFontSize(12);
        doc.setTextColor('#05fcfc');
        doc.text('PROCESSES - Executed', 105, 23);

        // Get and format TaskExec
        const bodyTable = [];
        let elem = [];
        const list = this.gathered['taskexec'];

        for (const i in list) {
            if (list[i]['module']) {
                elem = [list[i]['module'],
                        list[i]['param'],
                        list[i]['from'],
                        list[i]['score'],
                        list[i]['state']];
                bodyTable.push(elem);
            }
        }

        autoTable(doc, {
             head: [['Module', 'Param', 'Exec by', 'Score', 'State']],
             body: bodyTable,
             headStyles: {fillColor: '#50fcfc',
                          cellPadding: {top: 3, right: 3, bottom: 3, left: 3},
                          lineWidth: 1,
                          halign: 'center',
                          textColor: '#000000',
                          lineColor: '#1A1A1A'},
             bodyStyles: {fillColor: '#1A1A1A',
                          cellPadding: {top: 3, right: 3, bottom: 3, left: 3},
                          lineWidth: 1,
                          textColor: '#50fcfc',
                          lineColor: '#1A1A1A'},
             columnStyles: {
                 0: {fillColor: '#393f46'},
                 1: {fillColor: '#22262a'},
                 2: {fillColor: '#393f46'},
                 3: {fillColor: '#22262a'},
                 4: {fillColor: '#393f46'},
             },
             margin: {top: 40},
        });

        /////////////////////////////////////////////////////////////////
        // EmailrepIO module report
        /////////////////////////////////////////////////////////////////
        if (this.gathered['emailrep'] &&
            this.gathered['emailrep']['result'] &&
            this.gathered['emailrep']['result'].length > 3) {

            this.reportMessage = 'EmailrepIO module...'
            // moduleHeight = 80;

            // Validate pageHeight
            // if ( hl + moduleHeight > pageHeight) {
            //     doc.addPage();
            //     hl = 20;
            // }

            let emailrep = false;

            doc.addPage();
            doc.setFontSize(25);
            hl = 40;

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('MODULE - EmailRepIO', 105, 23);

            // Information table
            if (this.gathered['emailrep'] &&
                this.gathered['emailrep']['result'] &&
                this.gathered['emailrep']['result'][4] &&
                this.gathered['emailrep']['result'][4]['graphic'] &&
                this.gathered['emailrep']['result'][4]['graphic'][0] &&
                this.gathered['emailrep']['result'][4]['graphic'][0]['details'] &&
                this.gathered['emailrep']['result'][4]['graphic'][0]['details'].length > 1) {

                this.reportMessage = 'EmailrepIO module...(Details)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divEmailrepInfo');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                emailrep = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['emailrep']['result'][4]['graphic'][0]['details'];

                for (const i in list) {
                    if (list[i]['title'] !== 'EmailRep') {
                        elem = [list[i]['title'], list[i]['subtitle']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                }
            }

            hl = hl + 10;

            // Information table
            if (this.gathered['emailrep'] &&
                this.gathered['emailrep']['result'] &&
                this.gathered['emailrep']['result'][4] &&
                this.gathered['emailrep']['result'][4]['graphic'] &&
                this.gathered['emailrep']['result'][4]['graphic'][1] &&
                this.gathered['emailrep']['result'][4]['graphic'][1]['social'] &&
                this.gathered['emailrep']['result'][4]['graphic'][1]['social'].length > 1) {

                this.reportMessage = 'EmailrepIO module...(Social)'

                svg = this.nbCardContainer.nativeElement.querySelector('#divEmailrepSocial');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                emailrep = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['emailrep']['result'][4]['graphic'][1]['social'];

                for (const i in list) {
                    if (list[i]['title'] !== 'EmailRep') {
                        elem = [list[i]['title']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Social networks']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                }
            }

            if (!emailrep) {
                doc.setLineWidth(15);
                doc.setDrawColor('#00000');
                doc.line(20, 105, 190, 105);
                doc.line(20, 155, 190, 155);
                img.src = 'assets/images/ban.png';
                doc.addImage(img, 'png', 10, 105, 190, 50);
            }

            hl = hl + 10;
        }

        /////////////////////////////////////////////////////////////////
        // Fullcontact module report
        /////////////////////////////////////////////////////////////////
        if (this.gathered['fullcontact'] &&
            this.gathered['fullcontact']['result'] &&
            this.gathered['fullcontact']['result'].length > 3) {

            this.reportMessage = 'Fullcontact module...'

            let fullcontact = false;

            doc.addPage();
            doc.setFontSize(25);
            hl = 40;

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('MODULE - Fullcontact', 105, 23);

            // Information table
            if (this.gathered['fullcontact'] &&
                this.gathered['fullcontact']['result'] &&
                this.gathered['fullcontact']['result'][4] &&
                this.gathered['fullcontact']['result'][4]['graphic'] &&
                this.gathered['fullcontact']['result'][4]['graphic'][0] &&
                this.gathered['fullcontact']['result'][4]['graphic'][0]['social'] &&
                this.gathered['fullcontact']['result'][4]['graphic'][0]['social'].length > 1) {

                this.reportMessage = 'Fullcontact module...(Social)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divFullcontactGraphs');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                fullcontact = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['fullcontact']['result'][4]['graphic'][0]['social'];

                for (const i in list) {
                    if (list[i]['title'] !== 'Social') {
                        elem = [list[i]['title'], list[i]['subtitle']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 40, left: 100},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                }
            }

            hl = hl + 10;

            if (!fullcontact) {
                doc.setLineWidth(15);
                doc.setDrawColor('#00000');
                doc.line(20, 105, 190, 105);
                doc.line(20, 155, 190, 155);
                img.src = 'assets/images/ban.png';
                doc.addImage(img, 'png', 10, 105, 190, 50);
            }

            hl = hl + 10;
        }

        /////////////////////////////////////////////////////////////////
        // PDL module report
        /////////////////////////////////////////////////////////////////
        if (this.gathered['peopledatalabs'] &&
            this.gathered['peopledatalabs']['result'] &&
            this.gathered['peopledatalabs']['result'].length > 3) {

            this.reportMessage = 'PeopleDataLabs module...'
            // moduleHeight = 80;

            // Validate pageHeight
            // if ( hl + moduleHeight > pageHeight) {
            //     doc.addPage();
            //     hl = 20;
            // }

            let peopledatalabs = false;

            doc.addPage();
            doc.setFontSize(25);
            hl = 40;

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('MODULE - PeopleDataLabs', 105, 23);

            // Information table
            if (this.gathered['peopledatalabs'] &&
                this.gathered['peopledatalabs']['result'] &&
                this.gathered['peopledatalabs']['result'][4] &&
                this.gathered['peopledatalabs']['result'][4]['graphic'] &&
                this.gathered['peopledatalabs']['result'][4]['graphic'][0] &&
                this.gathered['peopledatalabs']['result'][4]['graphic'][0]['data'] &&
                this.gathered['peopledatalabs']['result'][4]['graphic'][0]['data'].length > 1) {

                this.reportMessage = 'PeopleDataLabs module...(Data)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divPeopledatalabsGraphs');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                peopledatalabs = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['peopledatalabs']['result'][4]['graphic'][0]['data'];

                for (const i in list) {
                    if (list[i]['title'] !== 'DataLab') {
                        elem = [list[i]['title'], list[i]['subtitle']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Information table
            if (this.gathered['peopledatalabs'] &&
                this.gathered['peopledatalabs']['result'] &&
                this.gathered['peopledatalabs']['result'][4] &&
                this.gathered['peopledatalabs']['result'][4]['graphic'] &&
                this.gathered['peopledatalabs']['result'][4]['graphic'][1] &&
                this.gathered['peopledatalabs']['result'][4]['graphic'][1]['social'] &&
                this.gathered['peopledatalabs']['result'][4]['graphic'][1]['social'].length > 1) {

                this.reportMessage = 'Peopledatalabs module...(Social)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divPeopledatalabsSocial');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                peopledatalabs = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['peopledatalabs']['result'][4]['graphic'][1]['social'];

                for (const i in list) {
                    if (list[i]['title'] !== 'Social') {
                        elem = [list[i]['title'], list[i]['subtitle']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Social networks', 'Username']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            if (!peopledatalabs) {
                doc.setLineWidth(15);
                doc.setDrawColor('#00000');
                doc.line(20, 105, 190, 105);
                doc.line(20, 155, 190, 155);
                img.src = 'assets/images/ban.png';
                doc.addImage(img, 'png', 10, 105, 190, 50);
            }

            hl = hl + 10;
        }

        /////////////////////////////////////////////////////////////////
        // Twitter and Twint module report
        /////////////////////////////////////////////////////////////////
        if (this.gathered['twitter'] &&
            this.gathered['twitter']['result'] &&
            this.gathered['twitter']['result'].length > 3) {

            this.reportMessage = 'Twitter module...'
            // moduleHeight = 80;

            // Validate pageHeight
            // if ( hl + moduleHeight > pageHeight) {
            //     doc.addPage();
            //     hl = 20;
            // }

            let twitter = false;

            doc.addPage();
            doc.setFontSize(25);
            hl = 40;

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('MODULE - Twitter', 105, 23);

            // Information table
            if (this.gathered['twitter'] &&
                this.gathered['twitter']['result'] &&
                this.gathered['twitter']['result'][4] &&
                this.gathered['twitter']['result'][4]['graphic'] &&
                this.gathered['twitter']['result'][4]['graphic'][0] &&
                this.gathered['twitter']['result'][4]['graphic'][0]['social'] &&
                this.gathered['twitter']['result'][4]['graphic'][0]['social'].length > 1) {

                this.reportMessage = 'Twitter module...(Social)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divTwitterSocial');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                twitter = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['twitter']['result'][4]['graphic'][0]['social'];

                for (const i in list) {
                    if (list[i]['title'] !== 'DataLab') {
                        elem = [list[i]['title'], list[i]['subtitle']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Information table
            if (this.gathered['twitter'] &&
                this.gathered['twitter']['result'] &&
                this.gathered['twitter']['result'][4] &&
                this.gathered['twitter']['result'][4]['graphic'] &&
                this.gathered['twitter']['result'][4]['graphic'][2] &&
                this.gathered['twitter']['result'][4]['graphic'][2]['popularity'] &&
                this.gathered['twitter']['result'][4]['graphic'][2]['popularity'].length > 1) {

                this.reportMessage = 'Twitter module...(Popularity)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divTwitterPopularity');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                twitter = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['twitter']['result'][4]['graphic'][2]['popularity'];

                for (const i in list) {
                    if (list[i]['value'] !== 'Social') {
                        elem = [list[i]['name'], list[i]['value']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Information table
            if (this.gathered['twitter'] &&
                this.gathered['twitter']['result'] &&
                this.gathered['twitter']['result'][4] &&
                this.gathered['twitter']['result'][4]['graphic'] &&
                this.gathered['twitter']['result'][4]['graphic'][1] &&
                this.gathered['twitter']['result'][4]['graphic'][1]['resume'] &&
                this.gathered['twitter']['result'][4]['graphic'][1]['resume']['children'].length > 1) {

                this.reportMessage = 'Twitter module...(Resume)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divTwitterResume');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                twitter = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['twitter']['result'][4]['graphic'][1]['resume']['children'];
                console.log('Resume', list);

                for (const i in list) {
                    if (list[i]['value'] !== 'Social') {
                        elem = [list[i]['name'], list[i]['value']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     // pageBreak: 'always',
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                     // didDrawPage: function (data) {
                     //     data.settings.margin.top = 40; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 65 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);
                hl = 40;
                const finalY = 40;

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Twitter', 105, 23);
            }

            // Information table
            if (this.gathered['twitter'] &&
                this.gathered['twitter']['result'] &&
                this.gathered['twitter']['result'][4] &&
                this.gathered['twitter']['result'][4]['graphic'] &&
                this.gathered['twitter']['result'][4]['graphic'][10] &&
                this.gathered['twitter']['result'][4]['graphic'][10]['time'] &&
                this.gathered['twitter']['result'][4]['graphic'][10]['time'].length > 1) {

                this.reportMessage = 'Twitter module...(Timeline)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divTwitterTimeline');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 25, hl, 160, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                twitter = true;

                hl = hl + 55
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 65 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);
                hl = 40;
                const finalY = 40;

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Twitter', 105, 23);
            }

            // Information table
            if (this.gathered['twitter'] &&
                this.gathered['twitter']['result'] &&
                this.gathered['twitter']['result'][4] &&
                this.gathered['twitter']['result'][4]['graphic'] &&
                this.gathered['twitter']['result'][4]['graphic'][5] &&
                this.gathered['twitter']['result'][4]['graphic'][5]['users'] &&
                this.gathered['twitter']['result'][4]['graphic'][5]['users'].length > 1) {

                this.reportMessage = 'Twitter module...(Users)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divTwitterUsers');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                twitter = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['twitter']['result'][4]['graphic'][5]['users'];
                list.sort((a, b)=> (a.subtitle < b.subtitle ? 1 : -1))

                for (const i in list) {
                    if (list[i]['title'] !== 'Users') {
                        elem = [list[i]['title'], list[i]['subtitle']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Users', 'Ocurrences']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     // pageBreak: 'always',
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            console.log(`ENTRANDO - SALTO: hl - ${hl} + 60 // pageHeight - ${pageHeight}`);
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Twitter', 105, 23);

                hl = 40;
            }
            console.log(`SALIENDO - SALTO: hl - ${hl} + 60 // pageHeight - ${pageHeight}`);

            // Information table
            if (this.gathered['twitter'] &&
                this.gathered['twitter']['result'] &&
                this.gathered['twitter']['result'][4] &&
                this.gathered['twitter']['result'][4]['graphic'] &&
                this.gathered['twitter']['result'][4]['graphic'][6] &&
                this.gathered['twitter']['result'][4]['graphic'][6]['tweetslist'] &&
                this.gathered['twitter']['result'][4]['graphic'][6]['tweetslist'].length > 1) {

                this.reportMessage = 'Twitter module...(TweetList)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divTwitterList');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 25, hl, 160, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                twitter = true;

                hl = hl + 55
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Twitter', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['twitter'] &&
                this.gathered['twitter']['result'] &&
                this.gathered['twitter']['result'][4] &&
                this.gathered['twitter']['result'][4]['graphic'] &&
                this.gathered['twitter']['result'][4]['graphic'][4] &&
                this.gathered['twitter']['result'][4]['graphic'][4]['hashtag'] &&
                this.gathered['twitter']['result'][4]['graphic'][4]['hashtag'].length > 1) {

                this.reportMessage = 'Twitter module...(Hashtag)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divTwitterHashtag');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                twitter = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['twitter']['result'][4]['graphic'][4]['hashtag'];

                for (const i in list) {
                    if (list[i]['title'] !== 'Users') {
                        elem = [list[i]['label'], list[i]['value']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Hashtag', 'Ocurrences']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Twitter', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['twitter'] &&
                this.gathered['twitter']['result'] &&
                this.gathered['twitter']['result'][4] &&
                this.gathered['twitter']['result'][4]['graphic'] &&
                this.gathered['twitter']['result'][4]['graphic'][8] &&
                this.gathered['twitter']['result'][4]['graphic'][8]['hour'] &&
                this.gathered['twitter']['result'][4]['graphic'][8]['hour'].length > 1) {

                this.reportMessage = 'Twitter module...(Hour)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divTwitterHour');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 60, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                twitter = true;

                hl = hl + 55;
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Twitter', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['twitter'] &&
                this.gathered['twitter']['result'] &&
                this.gathered['twitter']['result'][4] &&
                this.gathered['twitter']['result'][4]['graphic'] &&
                this.gathered['twitter']['result'][4]['graphic'][7] &&
                this.gathered['twitter']['result'][4]['graphic'][7]['week'] &&
                this.gathered['twitter']['result'][4]['graphic'][7]['week'].length > 1) {

                this.reportMessage = 'Twitter module...(Week)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divTwitterWeek');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 60, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                twitter = true;

                hl = hl + 55;
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Twitter', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['twitter'] &&
                this.gathered['twitter']['result'] &&
                this.gathered['twitter']['result'][4] &&
                this.gathered['twitter']['result'][4]['graphic'] &&
                this.gathered['twitter']['result'][4]['graphic'][9] &&
                this.gathered['twitter']['result'][4]['graphic'][9]['sources'] &&
                this.gathered['twitter']['result'][4]['graphic'][9]['sources'].length > 0) {

                this.reportMessage = 'Twitter (Twitter) module...(Source)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divTwitterSource');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                twitter = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['twitter']['result'][4]['graphic'][9]['sources'];

                for (const i in list) {
                    if (list[i]['title'] !== 'Users') {
                        elem = [list[i]['name'], list[i]['value']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Source', 'Qty']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Twitter', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['twitter'] &&
                this.gathered['twitter']['result'] &&
                this.gathered['twitter']['result'][4] &&
                this.gathered['twitter']['result'][4]['graphic'] &&
                this.gathered['twitter']['result'][4]['graphic'][11] &&
                this.gathered['twitter']['result'][4]['graphic'][11]['twvsrt'] &&
                this.gathered['twitter']['result'][4]['graphic'][11]['twvsrt'].length > 0) {

                this.reportMessage = 'Twitter (Twitter) module...(Tweets vs ReTweets)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divTwitterTwvsrt');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                twitter = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['twitter']['result'][4]['graphic'][11]['twvsrt'];

                for (const i in list) {
                    if (list[i]['title'] !== 'Users') {
                        elem = [list[i]['name'], list[i]['value']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            if (!twitter) {
                doc.setLineWidth(15);
                doc.setDrawColor('#00000');
                doc.line(20, 105, 190, 105);
                doc.line(20, 155, 190, 155);
                img.src = 'assets/images/ban.png';
                doc.addImage(img, 'png', 10, 105, 190, 50);
            }

            hl = hl + 10;
        }

        /////////////////////////////////////////////////////////////////
        // Instagram module report
        /////////////////////////////////////////////////////////////////
        if (this.gathered['instagram'] &&
            this.gathered['instagram']['result'] &&
            this.gathered['instagram']['result'].length > 3) {

            this.reportMessage = 'Instagram module...'

            let instagram = false;

            doc.addPage();
            doc.setFontSize(25);
            hl = 40;

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('MODULE - Instagram', 105, 23);

            // Information table
            if (this.gathered['instagram'] &&
                this.gathered['instagram']['result'] &&
                this.gathered['instagram']['result'][4] &&
                this.gathered['instagram']['result'][4]['graphic'] &&
                this.gathered['instagram']['result'][4]['graphic'][0] &&
                this.gathered['instagram']['result'][4]['graphic'][0]['instagram'] &&
                this.gathered['instagram']['result'][4]['graphic'][0]['instagram'].length > 1) {

                this.reportMessage = 'Instagram module...(Social)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divInstagramSocial');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                instagram = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['instagram']['result'][4]['graphic'][0]['instagram'];

                for (const i in list) {
                    if (list[i]['title'] !== 'Instagram') {
                        elem = [list[i]['title'], list[i]['subtitle']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // TODO: Images ??

            // Information table
            if (this.gathered['instagram'] &&
                this.gathered['instagram']['result'] &&
                this.gathered['instagram']['result'][4] &&
                this.gathered['instagram']['result'][4]['graphic'] &&
                this.gathered['instagram']['result'][4]['graphic'][3] &&
                this.gathered['instagram']['result'][4]['graphic'][3]['hashtags'] &&
                this.gathered['instagram']['result'][4]['graphic'][3]['hashtags'].length > 0) {

                this.reportMessage = 'Instagram module...(Hashtag)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divInstagramHashtag');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                instagram = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['instagram']['result'][4]['graphic'][3]['hashtags'];

                for (const i in list) {
                    if (list[i]['title'] !== 'Users') {
                        elem = [list[i]['label'], list[i]['value']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Hashtag', 'Ocurrences']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Instagram', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['instagram'] &&
                this.gathered['instagram']['result'] &&
                this.gathered['instagram']['result'][4] &&
                this.gathered['instagram']['result'][4]['graphic'] &&
                this.gathered['instagram']['result'][4]['graphic'][4] &&
                this.gathered['instagram']['result'][4]['graphic'][4]['mentions'] &&
                this.gathered['instagram']['result'][4]['graphic'][4]['mentions'].length > 0) {

                this.reportMessage = 'Instagram module...(Mentions)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divInstagramMention');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                instagram = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['instagram']['result'][4]['graphic'][4]['mentions'];

                for (const i in list) {
                    if (list[i]['title'] !== 'Users') {
                        elem = [list[i]['label'], list[i]['value']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Mention', 'Ocurrences']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Instagram', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['instagram'] &&
                this.gathered['instagram']['result'] &&
                this.gathered['instagram']['result'][4] &&
                this.gathered['instagram']['result'][4]['graphic'] &&
                this.gathered['instagram']['result'][4]['graphic'][5] &&
                this.gathered['instagram']['result'][4]['graphic'][5]['tagged'] &&
                this.gathered['instagram']['result'][4]['graphic'][5]['tagged'].length > 0) {

                this.reportMessage = 'Instagram module...(Tagged)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divInstagramTagged');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                instagram = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['instagram']['result'][4]['graphic'][5]['tagged'];

                for (const i in list) {
                    if (list[i]['title'] !== 'Users') {
                        elem = [list[i]['label'], list[i]['value']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Mention', 'Ocurrences']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,  
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Instagram', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['instagram'] &&
                this.gathered['instagram']['result'] &&
                this.gathered['instagram']['result'][4] &&
                this.gathered['instagram']['result'][4]['graphic'] &&
                this.gathered['instagram']['result'][4]['graphic'][6] &&
                this.gathered['instagram']['result'][4]['graphic'][6]['hour'] &&
                this.gathered['instagram']['result'][4]['graphic'][6]['hour'].length > 1) {

                this.reportMessage = 'Instagram module...(Hour)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divInstagramHour');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 60, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                instagram = true;

                hl = hl + 55;
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Instagram', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['instagram'] &&
                this.gathered['instagram']['result'] &&
                this.gathered['instagram']['result'][4] &&
                this.gathered['instagram']['result'][4]['graphic'] &&
                this.gathered['instagram']['result'][4]['graphic'][7] &&
                this.gathered['instagram']['result'][4]['graphic'][7]['week'] &&
                this.gathered['instagram']['result'][4]['graphic'][7]['week'].length > 1) {

                this.reportMessage = 'Instagram module...(Week)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divInstagramWeek');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 60, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                instagram = true;

                hl = hl + 55;
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Instagram', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['instagram'] &&
                this.gathered['instagram']['result'] &&
                this.gathered['instagram']['result'][4] &&
                this.gathered['instagram']['result'][4]['graphic'] &&
                this.gathered['instagram']['result'][4]['graphic'][1] &&
                this.gathered['instagram']['result'][4]['graphic'][1]['postslist'] &&
                this.gathered['instagram']['result'][4]['graphic'][1]['postslist'].length > 0) {

                this.reportMessage = 'Instagram module...(Post list)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divInstagramPosts');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                instagram = true;
                const bodyTable = [];
                let elem = [];
                const listlikes = this.gathered['instagram']['result'][4]['graphic'][1]['postslist'][0]['series'];
                const listcomm = this.gathered['instagram']['result'][4]['graphic'][1]['postslist'][1]['series'];

                for (const i in listlikes) {
                    elem = [listlikes[i]['name'], listlikes[i]['value'], listcomm[i]['value']];
                    bodyTable.push(elem);
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Post (Last)', 'Likes', 'Comments']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46'},
                         1: {fillColor: '#22262a'},
                         2: {fillColor: '#393f46'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Instagram', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['instagram'] &&
                this.gathered['instagram']['result'] &&
                this.gathered['instagram']['result'][4] &&
                this.gathered['instagram']['result'][4]['graphic'] &&
                this.gathered['instagram']['result'][4]['graphic'][8] &&
                this.gathered['instagram']['result'][4]['graphic'][8]['mediatype'] &&
                this.gathered['instagram']['result'][4]['graphic'][8]['mediatype'].length > 0) {

                this.reportMessage = 'Instagram module...(Mediatype)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divInstagramMediatype');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                instagram = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['instagram']['result'][4]['graphic'][8]['mediatype'];

                for (const i in list) {
                    if (list[i]['title'] !== 'Users') {
                        elem = [list[i]['name'], list[i]['value']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46'},
                         1: {fillColor: '#22262a'},
                         2: {fillColor: '#393f46'},
                         3: {fillColor: '#22262a'},
                         4: {fillColor: '#393f46'},
                         5: {fillColor: '#22262a'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Instagram', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['instagram'] &&
                this.gathered['instagram']['result'] &&
                this.gathered['instagram']['result'][4] &&
                this.gathered['instagram']['result'][4]['graphic'] &&
                this.gathered['instagram']['result'][4]['graphic'][2] &&
                this.gathered['instagram']['result'][4]['graphic'][2]['postsloc'] &&
                this.gathered['instagram']['result'][4]['graphic'][2]['postsloc'].length > 0) {

                this.reportMessage = 'Instagram module...(Posts location)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divInstagramMap');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 25, hl, 160, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                instagram = true;
                const bodyTable = [];
                let elem = [];
                let list = this.gathered['instagram']['result'][4]['graphic'][2]['postsloc'];

                for (const i in list) {
                    elem = [list[i]['Name'], list[i]['Caption'], list[i]['Accessability'], list[i]['Latitude'], list[i]['Longitude'], list[i]['Time']];
                    bodyTable.push(elem);
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Caption', 'Accessability', 'Lat', 'Long', 'Time']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46'},
                         1: {fillColor: '#22262a'},
                         2: {fillColor: '#393f46'},
                         3: {fillColor: '#22262a'},
                         4: {fillColor: '#393f46'},
                         5: {fillColor: '#22262a'},
                     },
                     margin: {top: 0, left: 15},
                     startY: hl + 60,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            if (!instagram) {
                doc.setLineWidth(15);
                doc.setDrawColor('#00000');
                doc.line(20, 105, 190, 105);
                doc.line(20, 155, 190, 155);
                img.src = 'assets/images/ban.png';
                doc.addImage(img, 'png', 10, 105, 190, 50);
            }

            hl = hl + 10;
        }

        /////////////////////////////////////////////////////////////////
        // Linkedin module report
        /////////////////////////////////////////////////////////////////
        if (this.gathered['linkedin'] &&
            this.gathered['linkedin']['result'] &&
            this.gathered['linkedin']['result'].length > 3) {

            this.reportMessage = 'Linkedin module...'

            let linkedin = false;

            doc.addPage();
            doc.setFontSize(25);
            hl = 40;

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('MODULE - Linkedin', 105, 23);

            // Information table
            if (this.gathered['linkedin'] &&
                this.gathered['linkedin']['result'] &&
                this.gathered['linkedin']['result'][4] &&
                this.gathered['linkedin']['result'][4]['graphic'] &&
                this.gathered['linkedin']['result'][4]['graphic'][0] &&
                this.gathered['linkedin']['result'][4]['graphic'][0]['social'] &&
                this.gathered['linkedin']['result'][4]['graphic'][0]['social'].length > 1) {

                this.reportMessage = 'Linkedin module...(Social)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divLinkedinGraphs');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                linkedin = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['linkedin']['result'][4]['graphic'][0]['social'];

                for (const i in list) {
                    if (list[i]['title'] !== 'Linkedin') {
                        elem = [list[i]['title'], list[i]['subtitle']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Information table
            if (this.gathered['linkedin'] &&
                this.gathered['linkedin']['result'] &&
                this.gathered['linkedin']['result'][4] &&
                this.gathered['linkedin']['result'][4]['graphic'] &&
                this.gathered['linkedin']['result'][4]['graphic'][1] &&
                this.gathered['linkedin']['result'][4]['graphic'][1]['skills'] &&
                this.gathered['linkedin']['result'][4]['graphic'][1]['skills']['children'] &&
                this.gathered['linkedin']['result'][4]['graphic'][1]['skills']['children'].length > 0) {

                this.reportMessage = 'Linkedin module...(Skills)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divLinkedinBubble');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                linkedin = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['linkedin']['result'][4]['graphic'][1]['skills']['children'];

                for (const i in list) {
                    elem = [list[i]['name'], list[i]['count']];
                    bodyTable.push(elem);
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Area', 'Skill']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Linkedin', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['linkedin'] &&
                this.gathered['linkedin']['result'] &&
                this.gathered['linkedin']['result'][4] &&
                this.gathered['linkedin']['result'][4]['graphic'] &&
                this.gathered['linkedin']['result'][4]['graphic'][2] &&
                this.gathered['linkedin']['result'][4]['graphic'][2]['certificationView'] &&
                this.gathered['linkedin']['result'][4]['graphic'][2]['certificationView'].length > 0) {

                this.reportMessage = 'Linkedin module...(Certifications)'

                // Image

                linkedin = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['linkedin']['result'][4]['graphic'][2]['certificationView'];

                for (const i in list) {
                    elem = [list[i]['name'], list[i]['desc']];
                    bodyTable.push(elem);
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Certification', 'Description']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 5, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 5, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46'},
                         1: {fillColor: '#22262a'},
                     },
                     margin: {top: 0, left: 15},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                hl = finalY;
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Linkedin', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['linkedin'] &&
                this.gathered['linkedin']['result'] &&
                this.gathered['linkedin']['result'][4] &&
                this.gathered['linkedin']['result'][4]['graphic'] &&
                this.gathered['linkedin']['result'][4]['graphic'][3] &&
                this.gathered['linkedin']['result'][4]['graphic'][3]['positionGroupView'] &&
                this.gathered['linkedin']['result'][4]['graphic'][3]['positionGroupView'].length > 0) {

                this.reportMessage = 'Linkedin module...(Positions)'

                // Image

                linkedin = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['linkedin']['result'][4]['graphic'][3]['positionGroupView'];

                for (const i in list) {
                    elem = [list[i]['label']];
                    bodyTable.push(elem);
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Positions']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46'},
                         1: {fillColor: '#22262a'},
                     },
                     margin: {top: 0, left: 50, right: 50},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            if (!linkedin) {
                doc.setLineWidth(15);
                doc.setDrawColor('#00000');
                doc.line(20, 105, 190, 105);
                doc.line(20, 155, 190, 155);
                img.src = 'assets/images/ban.png';
                doc.addImage(img, 'png', 10, 105, 190, 50);
            }

            hl = hl + 10;
        }

        /////////////////////////////////////////////////////////////////
        // Github module report
        /////////////////////////////////////////////////////////////////
        if (this.gathered['github'] &&
            this.gathered['github']['result'] &&
            this.gathered['github']['result'].length > 3) {

            this.reportMessage = 'Instagram module...'

            let github = false;

            doc.addPage();
            doc.setFontSize(25);
            hl = 40;

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('MODULE - Github', 105, 23);

            // Information table
            if (this.gathered['github'] &&
                this.gathered['github']['result'] &&
                this.gathered['github']['result'][4] &&
                this.gathered['github']['result'][4]['graphic'] &&
                this.gathered['github']['result'][4]['graphic'][0] &&
                this.gathered['github']['result'][4]['graphic'][0]['github'] &&
                this.gathered['github']['result'][4]['graphic'][0]['github'].length > 1) {

                this.reportMessage = 'Github module...(Social)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divGithubGraphs');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                github = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['github']['result'][4]['graphic'][0]['github'];

                for (const i in list) {
                    if (list[i]['title'] !== 'Github') {
                        elem = [list[i]['title'], list[i]['subtitle']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Information table
            if (this.gathered['github'] &&
                this.gathered['github']['result'] &&
                this.gathered['github']['result'][4] &&
                this.gathered['github']['result'][4]['graphic'] &&
                this.gathered['github']['result'][4]['graphic'][1] &&
                this.gathered['github']['result'][4]['graphic'][1]['cal_actual'] &&
                this.gathered['github']['result'][4]['graphic'][1]['cal_actual'].length > 0) {

                this.reportMessage = 'Github module...(Calendar)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divGithubCalendar');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 25, hl, 160, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                github = true;
            }

            if (!github) {
                doc.setLineWidth(15);
                doc.setDrawColor('#00000');
                doc.line(20, 105, 190, 105);
                doc.line(20, 155, 190, 155);
                img.src = 'assets/images/ban.png';
                doc.addImage(img, 'png', 10, 105, 190, 50);
            }

            hl = hl + 10;
        }

        /////////////////////////////////////////////////////////////////
        // Keybase module report
        /////////////////////////////////////////////////////////////////
        if (this.gathered['keybase'] &&
            this.gathered['keybase']['result'] &&
            this.gathered['keybase']['result'].length > 3) {

            this.reportMessage = 'Keybase module...'

            let keybase = false;

            doc.addPage();
            doc.setFontSize(25);
            hl = 40;

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('MODULE - Keybase', 105, 23);

            // Information table
            if (this.gathered['keybase'] &&
                this.gathered['keybase']['result'] &&
                this.gathered['keybase']['result'][4] &&
                this.gathered['keybase']['result'][4]['graphic'] &&
                this.gathered['keybase']['result'][4]['graphic'][0] &&
                this.gathered['keybase']['result'][4]['graphic'][0]['keysocial'] &&
                this.gathered['keybase']['result'][4]['graphic'][0]['keysocial'].length > 1) {

                this.reportMessage = 'Keybase module...(Social)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divKeybaseSocial');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                keybase = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['keybase']['result'][4]['graphic'][0]['keysocial'];

                for (const i in list) {
                    if (list[i]['title'] !== 'KeybaseSocial') {
                        elem = [list[i]['title'], list[i]['subtitle']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Information table
            if (this.gathered['keybase'] &&
                this.gathered['keybase']['result'] &&
                this.gathered['keybase']['result'][4] &&
                this.gathered['keybase']['result'][4]['graphic'] &&
                this.gathered['keybase']['result'][4]['graphic'][1] &&
                this.gathered['keybase']['result'][4]['graphic'][1]['devices'] &&
                this.gathered['keybase']['result'][4]['graphic'][1]['devices'].length > 1) {

                this.reportMessage = 'Keybase module...(Devices)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divKeybaseDevices');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                keybase = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['keybase']['result'][4]['graphic'][1]['devices'];

                for (const i in list) {
                    if (list[i]['title'] !== 'Devices') {
                        elem = [list[i]['title'], list[i]['subtitle']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            if (!keybase) {
                doc.setLineWidth(15);
                doc.setDrawColor('#00000');
                doc.line(20, 105, 190, 105);
                doc.line(20, 155, 190, 155);
                img.src = 'assets/images/ban.png';
                doc.addImage(img, 'png', 10, 105, 190, 50);
            }

            hl = hl + 10;
        }

        /////////////////////////////////////////////////////////////////
        // Spotify module report
        /////////////////////////////////////////////////////////////////
        if (this.gathered['spotify'] &&
            this.gathered['spotify']['result'] &&
            this.gathered['spotify']['result'].length > 3) {

            this.reportMessage = 'Spotify module...'

            let spotify = false;

            doc.addPage();
            doc.setFontSize(25);
            hl = 40;

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('MODULE - Spotify', 105, 23);

            // Information table
            if (this.gathered['spotify'] &&
                this.gathered['spotify']['result'] &&
                this.gathered['spotify']['result'][4] &&
                this.gathered['spotify']['result'][4]['graphic'] &&
                this.gathered['spotify']['result'][4]['graphic'][0] &&
                this.gathered['spotify']['result'][4]['graphic'][0]['social'] &&
                this.gathered['spotify']['result'][4]['graphic'][0]['social'].length > 1) {

                this.reportMessage = 'Spotify module...(Social)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divSpotifySocial');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                spotify = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['spotify']['result'][4]['graphic'][0]['social'];

                for (const i in list) {
                    if (list[i]['title'] !== 'Spotify') {
                        elem = [list[i]['title'], list[i]['subtitle']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // TODO : Playlist

            // Information table
            if (this.gathered['spotify'] &&
                this.gathered['spotify']['result'] &&
                this.gathered['spotify']['result'][4] &&
                this.gathered['spotify']['result'][4]['graphic'] &&
                this.gathered['spotify']['result'][4]['graphic'][2] &&
                this.gathered['spotify']['result'][4]['graphic'][2]['autors'] &&
                this.gathered['spotify']['result'][4]['graphic'][2]['autors'].length > 1) {

                this.reportMessage = 'Spotify module...(Authors)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divSpotifyAutors');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                spotify = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['spotify']['result'][4]['graphic'][2]['autors'];
                list.sort((a, b)=> (a.value < b.value ? 1 : -1))

                let a = 0;
                for (const i in list) {
                    if (a === 16) {
                        break;
                    }
                    elem = [list[i]['label'], list[i]['value']];
                    bodyTable.push(elem);
                    a = a + 1;
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Author', 'Ocurrences']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     // pageBreak: 'always',
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Spotify', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['spotify'] &&
                this.gathered['spotify']['result'] &&
                this.gathered['spotify']['result'][4] &&
                this.gathered['spotify']['result'][4]['graphic'] &&
                this.gathered['spotify']['result'][4]['graphic'][3] &&
                this.gathered['spotify']['result'][4]['graphic'][3]['words'] &&
                this.gathered['spotify']['result'][4]['graphic'][3]['words'].length > 1) {

                this.reportMessage = 'Spotify module...(Words)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divSpotifyWords');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                spotify = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['spotify']['result'][4]['graphic'][3]['words'];
                list.sort((a, b)=> (a.value < b.value ? 1 : -1))

                let a = 0;
                for (const i in list) {
                    if (a === 16) {
                        break;
                    }
                    elem = [list[i]['label'], list[i]['value']];
                    bodyTable.push(elem);
                    a = a + 1;
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Word', 'Ocurrences']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     // pageBreak: 'always',
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Spotify', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['spotify'] &&
                this.gathered['spotify']['result'] &&
                this.gathered['spotify']['result'][4] &&
                this.gathered['spotify']['result'][4]['graphic'] &&
                this.gathered['spotify']['result'][4]['graphic'][4] &&
                this.gathered['spotify']['result'][4]['graphic'][4]['lang'] &&
                this.gathered['spotify']['result'][4]['graphic'][4]['lang'].length > 1) {

                this.reportMessage = 'Spotify module...(Language)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divSpotifyLang');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                spotify = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['spotify']['result'][4]['graphic'][4]['lang'];
                list.sort((a, b)=> (a.value < b.value ? 1 : -1))

                let a = 0;
                for (const i in list) {
                    if (a === 7) {
                        break;
                    }
                    elem = [list[i]['name'], list[i]['value']];
                    bodyTable.push(elem);
                    a = a + 1;
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }
            if (!spotify) {
                doc.setLineWidth(15);
                doc.setDrawColor('#00000');
                doc.line(20, 105, 190, 105);
                doc.line(20, 155, 190, 155);
                img.src = 'assets/images/ban.png';
                doc.addImage(img, 'png', 10, 105, 190, 50);
            }

            hl = hl + 10;
        }

        /////////////////////////////////////////////////////////////////
        // Reddit module report
        /////////////////////////////////////////////////////////////////
        if (this.gathered['reddit'] &&
            this.gathered['reddit']['result'] &&
            this.gathered['reddit']['result'].length > 3) {

            this.reportMessage = 'Reddit module...'

            let reddit = false;

            doc.addPage();
            doc.setFontSize(25);
            hl = 40;

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('MODULE - Reddit', 105, 23);

            // Information table
            if (this.gathered['reddit'] &&
                this.gathered['reddit']['result'] &&
                this.gathered['reddit']['result'][4] &&
                this.gathered['reddit']['result'][4]['graphic'] &&
                this.gathered['reddit']['result'][4]['graphic'][0] &&
                this.gathered['reddit']['result'][4]['graphic'][0]['social'] &&
                this.gathered['reddit']['result'][4]['graphic'][0]['social'].length > 1) {

                this.reportMessage = 'Reddit module...(Social)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divRedditSocial');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                reddit = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['reddit']['result'][4]['graphic'][0]['social'];

                for (const i in list) {
                    if (list[i]['title'] !== 'Reddit') {
                        elem = [list[i]['title'], list[i]['subtitle']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Information table
            if (this.gathered['reddit'] &&
                this.gathered['reddit']['result'] &&
                this.gathered['reddit']['result'][4] &&
                this.gathered['reddit']['result'][4]['graphic'] &&
                this.gathered['reddit']['result'][4]['graphic'][1] &&
                this.gathered['reddit']['result'][4]['graphic'][1]['hour'] &&
                this.gathered['reddit']['result'][4]['graphic'][1]['hour'].length > 0) {

                this.reportMessage = 'Reddit module...(Hour)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divRedditHour');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 60, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                reddit = true;

                hl = hl + 55;
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Reddit', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['reddit'] &&
                this.gathered['reddit']['result'] &&
                this.gathered['reddit']['result'][4] &&
                this.gathered['reddit']['result'][4]['graphic'] &&
                this.gathered['reddit']['result'][4]['graphic'][2] &&
                this.gathered['reddit']['result'][4]['graphic'][2]['week'] &&
                this.gathered['reddit']['result'][4]['graphic'][2]['week'].length > 0) {

                this.reportMessage = 'Reddit module...(Week)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divRedditWeek');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 60, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                instagram = true;

                hl = hl + 55;
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Reddit', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['reddit'] &&
                this.gathered['reddit']['result'] &&
                this.gathered['reddit']['result'][4] &&
                this.gathered['reddit']['result'][4]['graphic'] &&
                this.gathered['reddit']['result'][4]['graphic'][3] &&
                this.gathered['reddit']['result'][4]['graphic'][3]['topics'] &&
                this.gathered['reddit']['result'][4]['graphic'][3]['topics']['children'] &&
                this.gathered['reddit']['result'][4]['graphic'][3]['topics']['children'].length > 0) {

                this.reportMessage = 'Reddit module...(Topics)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divRedditBubble');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                reddit = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['reddit']['result'][4]['graphic'][3]['topics']['children'];
                list.sort((a, b)=> (a.value < b.value ? 1 : -1))

                let a = 0;
                for (const i in list) {
                    if (a === 16) {
                        break;
                    }
                    elem = [list[i]['name'], list[i]['value']];
                    bodyTable.push(elem);
                    a = a + 1;
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Topic', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }
            if (!reddit) {
                doc.setLineWidth(15);
                doc.setDrawColor('#00000');
                doc.line(20, 105, 190, 105);
                doc.line(20, 155, 190, 155);
                img.src = 'assets/images/ban.png';
                doc.addImage(img, 'png', 10, 105, 190, 50);
            }

            hl = hl + 10;
        }

        /////////////////////////////////////////////////////////////////
        // Tiktok module report
        /////////////////////////////////////////////////////////////////
        if (this.gathered['tiktok'] &&
            this.gathered['tiktok']['result'] &&
            this.gathered['tiktok']['result'].length > 3) {

            this.reportMessage = 'Tiktok module...'

            let tiktok = false;

            doc.addPage();
            doc.setFontSize(25);
            hl = 40;

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('MODULE - Tiktok', 105, 23);

            // Information table
            if (this.gathered['tiktok'] &&
                this.gathered['tiktok']['result'] &&
                this.gathered['tiktok']['result'][4] &&
                this.gathered['tiktok']['result'][4]['graphic'] &&
                this.gathered['tiktok']['result'][4]['graphic'][0] &&
                this.gathered['tiktok']['result'][4]['graphic'][0]['tiktok'] &&
                this.gathered['tiktok']['result'][4]['graphic'][0]['tiktok'].length > 1) {

                this.reportMessage = 'Tiktok module...(Social)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divTiktokSocial');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                tiktok = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['tiktok']['result'][4]['graphic'][0]['tiktok'];

                for (const i in list) {
                    if (list[i]['title'] !== 'Tiktok') {
                        elem = [list[i]['title'], list[i]['subtitle']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            if (!tiktok) {
                doc.setLineWidth(15);
                doc.setDrawColor('#00000');
                doc.line(20, 105, 190, 105);
                doc.line(20, 155, 190, 155);
                img.src = 'assets/images/ban.png';
                doc.addImage(img, 'png', 10, 105, 190, 50);
            }

            hl = hl + 10;
        }

        /////////////////////////////////////////////////////////////////
        // Twitch module report
        /////////////////////////////////////////////////////////////////
        if (this.gathered['twitch'] &&
            this.gathered['twitch']['result'] &&
            this.gathered['twitch']['result'].length > 3) {

            this.reportMessage = 'Twitch module...'

            let twitch = false;

            doc.addPage();
            doc.setFontSize(25);
            hl = 40;

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('MODULE - Twitch', 105, 23);

            // Information table
            if (this.gathered['twitch'] &&
                this.gathered['twitch']['result'] &&
                this.gathered['twitch']['result'][4] &&
                this.gathered['twitch']['result'][4]['graphic'] &&
                this.gathered['twitch']['result'][4]['graphic'][0] &&
                this.gathered['twitch']['result'][4]['graphic'][0]['social'] &&
                this.gathered['twitch']['result'][4]['graphic'][0]['social'].length > 1) {

                this.reportMessage = 'Twitch module...(Social)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divTwitchSocial');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                twitch = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['twitch']['result'][4]['graphic'][0]['social'];

                for (const i in list) {
                    if (list[i]['title'] !== 'Twitch') {
                        elem = [list[i]['title'], list[i]['subtitle']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Information table
            if (this.gathered['twitch'] &&
                this.gathered['twitch']['result'] &&
                this.gathered['twitch']['result'][4] &&
                this.gathered['twitch']['result'][4]['graphic'] &&
                this.gathered['twitch']['result'][4]['graphic'][5] &&
                this.gathered['twitch']['result'][4]['graphic'][5]['hour'] &&
                this.gathered['twitch']['result'][4]['graphic'][5]['hour'].length > 0) {

                this.reportMessage = 'Twitch module...(Hour)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divTwitchHour');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 60, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                twitch = true;

                hl = hl + 55;
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Twitch', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['twitch'] &&
                this.gathered['twitch']['result'] &&
                this.gathered['twitch']['result'][4] &&
                this.gathered['twitch']['result'][4]['graphic'] &&
                this.gathered['twitch']['result'][4]['graphic'][6] &&
                this.gathered['twitch']['result'][4]['graphic'][6]['time'] &&
                this.gathered['twitch']['result'][4]['graphic'][6]['time'].length > 0) {

                this.reportMessage = 'Twitch module...(Timeline)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divTwitchTimeline');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 60, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                twitch = true;

                hl = hl + 55;
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Twitch', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['twitch'] &&
                this.gathered['twitch']['result'] &&
                this.gathered['twitch']['result'][4] &&
                this.gathered['twitch']['result'][4]['graphic'] &&
                this.gathered['twitch']['result'][4]['graphic'][4] &&
                this.gathered['twitch']['result'][4]['graphic'][4]['week'] &&
                this.gathered['twitch']['result'][4]['graphic'][4]['week'].length > 0) {

                this.reportMessage = 'Twitch module...(Week)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divTwitchWeek');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 60, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                instagram = true;

                hl = hl + 55;
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Twitch', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['twitch'] &&
                this.gathered['twitch']['result'] &&
                this.gathered['twitch']['result'][4] &&
                this.gathered['twitch']['result'][4]['graphic'] &&
                this.gathered['twitch']['result'][4]['graphic'][2] &&
                this.gathered['twitch']['result'][4]['graphic'][2]['duration'] &&
                this.gathered['twitch']['result'][4]['graphic'][2]['duration'].length > 0) {

                this.reportMessage = 'Twitch module...(Duration)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divTwitchDuration');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 60, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                instagram = true;

                hl = hl + 55;
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Twitch', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['twitch'] &&
                this.gathered['twitch']['result'] &&
                this.gathered['twitch']['result'][4] &&
                this.gathered['twitch']['result'][4]['graphic'] &&
                this.gathered['twitch']['result'][4]['graphic'][1] && 
                this.gathered['twitch']['result'][4]['graphic'][1]['table'] &&
                this.gathered['twitch']['result'][4]['graphic'][1]['table'].length > 0) {

                this.reportMessage = 'Twitch module...(Table)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divTwitchVideos');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 25, hl, 160, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                hl = hl + 60;

                twitch = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['twitch']['result'][4]['graphic'][1]['table'];
                list.sort((a, b)=> (a.value < b.value ? 1 : -1))

                let a = 0;
                for (const i in list) {
                    if (a === 16) {
                        break;
                    }
                    elem = [list[i]['created'], list[i]['title'], list[i]['description'], list[i]['url']];
                    bodyTable.push(elem);
                    a = a + 1;
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Created', 'Title', 'Description', 'url']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 7,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 30},
                         1: {fillColor: '#22262a', cellWidth: 50},
                         2: {fillColor: '#393f46'},
                         3: {fillColor: '#22262a'},
                     },
                     margin: {top: 0, left: 15},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            if (!twitch) {
                doc.setLineWidth(15);
                doc.setDrawColor('#00000');
                doc.line(20, 105, 190, 105);
                doc.line(20, 155, 190, 155);
                img.src = 'assets/images/ban.png';
                doc.addImage(img, 'png', 10, 105, 190, 50);
            }

            hl = hl + 10;
        }

        /////////////////////////////////////////////////////////////////
        // Leaks and Password module report
        /////////////////////////////////////////////////////////////////
        if (this.gathered['leaklookup'] &&
            this.gathered['leaklookup']['result'] &&
            this.gathered['leaklookup']['result'].length > 3 &&
            this.gathered['leaklookup']['result'][4] &&
            this.gathered['leaklookup']['result'][4]['graphic'] &&
            this.gathered['leaklookup']['result'][4]['graphic'][0] &&
            this.gathered['leaklookup']['result'][4]['graphic'][0]['email'] &&
            this.gathered['leaklookup']['result'][4]['graphic'][0]['email'].length > 1) {

            this.reportMessage = 'Leaklookup module...'

            let leaks = false;

            doc.addPage();
            doc.setFontSize(25);
            hl = 40;

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('MODULE - Leaks and Passwords', 105, 23);

            // Information table
            if (this.gathered['leaklookup'] &&
                this.gathered['leaklookup']['result'] &&
                this.gathered['leaklookup']['result'][4] &&
                this.gathered['leaklookup']['result'][4]['graphic'] &&
                this.gathered['leaklookup']['result'][4]['graphic'][0] &&
                this.gathered['leaklookup']['result'][4]['graphic'][0]['email'] &&
                this.gathered['leaklookup']['result'][4]['graphic'][0]['email'].length > 1) {

                this.reportMessage = 'Leaks and Passwords module...(Leaklookup)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divLeaklookupEmail');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                leaks = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['leaklookup']['result'][4]['graphic'][0]['email'];

                for (const i in list) {
                    if (list[i]['title'] !== 'Leak') {
                        for (const j in list[i]['value']) {
                            elem = [list[i]['name'], list[i]['value'][j]['name'], list[i]['value'][j]['value']];
                            bodyTable.push(elem);
                        }
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Site', 'Name', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46'},
                         1: {fillColor: '#22262a'},
                         2: {fillColor: '#393f46'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            if (!leaks) {
                doc.setLineWidth(15);
                doc.setDrawColor('#00000');
                doc.line(20, 105, 190, 105);
                doc.line(20, 155, 190, 155);
                img.src = 'assets/images/ban.png';
                doc.addImage(img, 'png', 10, 105, 190, 50);
            }

            hl = hl + 10;
        }

        /////////////////////////////////////////////////////////////////
        // Holehe module report
        /////////////////////////////////////////////////////////////////
        if (this.gathered['holehe'] &&
            this.gathered['holehe']['result'] &&
            this.gathered['holehe']['result'].length > 3) {

            this.reportMessage = 'Holehe module...'

            let holehe = false;

            doc.addPage();
            doc.setFontSize(25);
            hl = 40;

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('MODULE - Holehe', 105, 23);

            // Information table
            if (this.gathered['holehe'] &&
                this.gathered['holehe']['result'] &&
                this.gathered['holehe']['result'][4] &&
                this.gathered['holehe']['result'][4]['graphic'] &&
                this.gathered['holehe']['result'][4]['graphic'][0] && 
                this.gathered['holehe']['result'][4]['graphic'][0]['holehe'] &&
                this.gathered['holehe']['result'][4]['graphic'][0]['holehe'].length > 1) {

                this.reportMessage = 'Holehe module...'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divHolehe');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 25, hl, 160, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                hl = hl + 60;

                holehe = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['holehe']['result'][4]['graphic'][1]['lists'];

                for (const i in list) {
                    if (list[i]['exists'] === 'true') {
                        elem = [list[i]['title'], list[i]['exists'], list[i]['emailrecovery'], list[i]['phoneNumber'], list[i]['others']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Title', 'Exist', 'EmailRecovery', 'PhoneNumber', 'Others']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 7,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46'},
                         1: {fillColor: '#22262a'},
                         2: {fillColor: '#393f46'},
                         3: {fillColor: '#22262a'},
                         4: {fillColor: '#393f46'},
                     },
                     margin: {top: 0, left: 15},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            if (!holehe) {
                doc.setLineWidth(15);
                doc.setDrawColor('#00000');
                doc.line(20, 105, 190, 105);
                doc.line(20, 155, 190, 155);
                img.src = 'assets/images/ban.png';
                doc.addImage(img, 'png', 10, 105, 190, 50);
            }

            hl = hl + 10;
        }

        /////////////////////////////////////////////////////////////////
        // Sherlock module report
        /////////////////////////////////////////////////////////////////
        if (this.gathered['sherlock'] &&
            this.gathered['sherlock']['result'] &&
            this.gathered['sherlock']['result'].length > 3) {

            this.reportMessage = 'Sherlock module...'

            let sherlock = false;

            doc.addPage();
            doc.setFontSize(25);
            hl = 40;

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('MODULE - Sherlock', 105, 23);

            // Information table
            if (this.gathered['sherlock'] &&
                this.gathered['sherlock']['result'] &&
                this.gathered['sherlock']['result'][4] &&
                this.gathered['sherlock']['result'][4]['graphic'] &&
                this.gathered['sherlock']['result'][4]['graphic'][0] && 
                this.gathered['sherlock']['result'][4]['graphic'][0]['sherlock'] &&
                this.gathered['sherlock']['result'][4]['graphic'][0]['sherlock'].length > 1) {

                this.reportMessage = 'Sherlock module...'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divSherlock');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 25, hl, 160, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                hl = hl + 60;

                sherlock = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['sherlock']['result'][4]['graphic'][1]['lists'];

                for (const i in list) {
                    if (list[i]['status'] === 200) {
                        elem = [list[i]['title'], list[i]['subtitle'], list[i]['status']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Site', 'URL', 'Status']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 7,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46'},
                         1: {fillColor: '#22262a'},
                         2: {fillColor: '#393f46'},
                     },
                     margin: {top: 0, left: 15},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            if (!sherlock) {
                doc.setLineWidth(15);
                doc.setDrawColor('#00000');
                doc.line(20, 105, 190, 105);
                doc.line(20, 155, 190, 155);
                img.src = 'assets/images/ban.png';
                doc.addImage(img, 'png', 10, 105, 190, 50);
            }

            hl = hl + 10;
        }

        /////////////////////////////////////////////////////////////////
        // Search module report
        /////////////////////////////////////////////////////////////////
        if (this.gathered['search'] &&
            this.gathered['search']['result'] &&
            this.gathered['search']['result'].length > 3) {

            this.reportMessage = 'Search module...'

            let search = false;

            doc.addPage();
            doc.setFontSize(25);
            hl = 40;

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('MODULE - Search', 105, 23);

            // Information table
            if (this.gathered['search'] &&
                this.gathered['search']['result'] &&
                this.gathered['search']['result'][4] &&
                this.gathered['search']['result'][4]['graphic'] &&
                this.gathered['search']['result'][4]['graphic'][5] && 
                this.gathered['search']['result'][4]['graphic'][5]['searches'] &&
                this.gathered['search']['result'][4]['graphic'][5]['searches'].length > 1) {

                this.reportMessage = 'Search module...'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divSearchSearches');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 25, hl, 160, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                hl = hl + 70;

                search = true;
            }

            // Information table
            if (this.gathered['search'] &&
                this.gathered['search']['result'] &&
                this.gathered['search']['result'][4] &&
                this.gathered['search']['result'][4]['graphic'] &&
                this.gathered['search']['result'][4]['graphic'][0] &&
                this.gathered['search']['result'][4]['graphic'][0]['names'] &&
                this.gathered['search']['result'][4]['graphic'][0]['names'].length > 0) {

                this.reportMessage = 'Search module...(Names)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divSearchNames');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                search = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['search']['result'][4]['graphic'][0]['names'];
                // list.sort((a, b)=> (a.value < b.value ? 1 : -1))

                // let a = 0;
                for (const i in list) {
                    // if (a === 16) {
                    //     break;
                    // }
                    elem = [list[i]['label']];
                    bodyTable.push(elem);
                    // a = a + 1;
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Names']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46'},
                     },
                     margin: {top: 0, left: 100},
                     // pageBreak: 'always',
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Search', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['search'] &&
                this.gathered['search']['result'] &&
                this.gathered['search']['result'][4] &&
                this.gathered['search']['result'][4]['graphic'] &&
                this.gathered['search']['result'][4]['graphic'][1] &&
                this.gathered['search']['result'][4]['graphic'][1]['username'] &&
                this.gathered['search']['result'][4]['graphic'][1]['username'].length > 0) {

                this.reportMessage = 'Search module...(Usernames)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divSearchUsernames');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                search = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['search']['result'][4]['graphic'][1]['username'];
                // list.sort((a, b)=> (a.value < b.value ? 1 : -1))

                // let a = 0;
                for (const i in list) {
                    // if (a === 16) {
                    //     break;
                    // }
                    elem = [list[i]['label']];
                    bodyTable.push(elem);
                    // a = a + 1;
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Usernames']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46'},
                     },
                     margin: {top: 0, left: 100},
                     // pageBreak: 'always',
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Search', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['search'] &&
                this.gathered['search']['result'] &&
                this.gathered['search']['result'][4] &&
                this.gathered['search']['result'][4]['graphic'] &&
                this.gathered['search']['result'][4]['graphic'][2] &&
                this.gathered['search']['result'][4]['graphic'][2]['social'] &&
                this.gathered['search']['result'][4]['graphic'][2]['social'].length > 0) {

                this.reportMessage = 'Search module...(Social)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divSearchSocial');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                search = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['search']['result'][4]['graphic'][2]['social'];
                // list.sort((a, b)=> (a.value < b.value ? 1 : -1))

                // let a = 0;
                for (const i in list) {
                    if (list[i]['title'] !== 'Social') {
                        elem = [list[i]['title'], list[i]['subtitle']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Social', 'Username']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46'},
                         1: {fillColor: '#22262a'},
                     },
                     margin: {top: 0, left: 100},
                     // pageBreak: 'always',
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Search', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['search'] &&
                this.gathered['search']['result'] &&
                this.gathered['search']['result'][4] &&
                this.gathered['search']['result'][4]['graphic'] &&
                this.gathered['search']['result'][4]['graphic'][6] &&
                this.gathered['search']['result'][4]['graphic'][6]['mentions'] &&
                this.gathered['search']['result'][4]['graphic'][6]['mentions'].length > 0) {

                this.reportMessage = 'Search module...(Mentions)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divSearchMentions');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                search = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['search']['result'][4]['graphic'][6]['mentions'];
                // list.sort((a, b)=> (a.value < b.value ? 1 : -1))

                // let a = 0;
                for (const i in list) {
                    // if (a === 16) {
                    //     break;
                    // }
                    elem = [list[i]['label']];
                    bodyTable.push(elem);
                    // a = a + 1;
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Mentions']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46'},
                     },
                     margin: {top: 0, left: 100},
                     // pageBreak: 'always',
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Search', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['search'] &&
                this.gathered['search']['result'] &&
                this.gathered['search']['result'][4] &&
                this.gathered['search']['result'][4]['graphic'] &&
                this.gathered['search']['result'][4]['graphic'][7] &&
                this.gathered['search']['result'][4]['graphic'][7]['hashtags'] &&
                this.gathered['search']['result'][4]['graphic'][7]['hashtags'].length > 0) {

                this.reportMessage = 'Search module...(Hashtags)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divSearchHashtag');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                search = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['search']['result'][4]['graphic'][7]['hashtags'];
                // list.sort((a, b)=> (a.value < b.value ? 1 : -1))

                // let a = 0;
                for (const i in list) {
                    // if (a === 16) {
                    //     break;
                    // }
                    elem = [list[i]['label']];
                    bodyTable.push(elem);
                    // a = a + 1;
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Hashtags']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46'},
                     },
                     margin: {top: 0, left: 100},
                     // pageBreak: 'always',
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Search', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['search'] &&
                this.gathered['search']['result'] &&
                this.gathered['search']['result'][4] &&
                this.gathered['search']['result'][4]['graphic'] &&
                this.gathered['search']['result'][4]['graphic'][8] &&
                this.gathered['search']['result'][4]['graphic'][8]['emails'] &&
                this.gathered['search']['result'][4]['graphic'][8]['emails'].length > 0) {

                this.reportMessage = 'Search module...(Emails)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divSearchEmails');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                search = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['search']['result'][4]['graphic'][8]['emails'];
                // list.sort((a, b)=> (a.value < b.value ? 1 : -1))

                // let a = 0;
                for (const i in list) {
                    // if (a === 16) {
                    //     break;
                    // }
                    elem = [list[i]['label']];
                    bodyTable.push(elem);
                    // a = a + 1;
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Emails']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46'},
                     },
                     margin: {top: 0, left: 100},
                     // pageBreak: 'always',
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Search', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['search'] &&
                this.gathered['search']['result'] &&
                this.gathered['search']['result'][4] &&
                this.gathered['search']['result'][4]['graphic'] &&
                this.gathered['search']['result'][4]['graphic'][4] && 
                this.gathered['search']['result'][4]['graphic'][4]['results'] &&
                this.gathered['search']['result'][4]['graphic'][4]['results'].length > 1) {

                this.reportMessage = 'Search module...(Analized results)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divSearchList');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 25, hl, 160, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                hl = hl + 60;

                search = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['search']['result'][4]['graphic'][4]['results'];

                for (const i in list) {
                    // console.log(list[i]['link'], list[i]['link'].toLowerCase(), list[i]['link'].substr(0,8))
                    if (list[i]['title'].toLowerCase() !== 'searcher' && list[i]['title'].substr(0,8) !== 'Detected') {
                        elem = [list[i]['link'], list[i]['title'], list[i]['desc'], list[i]['url']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Search', 'Title', 'Description', 'URL']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 2},
                                  lineWidth: 1,
                                  fontSize: 7,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 20},
                         1: {fillColor: '#22262a', cellWidth: 40},
                         2: {fillColor: '#393f46'},
                         3: {fillColor: '#22262a', cellWidth: 40},
                        //  4: {fillColor: '#393f46'},
                     },
                     margin: {top: 0, left: 15},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            if (!search) {
                doc.setLineWidth(15);
                doc.setDrawColor('#00000');
                doc.line(20, 105, 190, 105);
                doc.line(20, 155, 190, 155);
                img.src = 'assets/images/ban.png';
                doc.addImage(img, 'png', 10, 105, 190, 50);
            }

            hl = hl + 10;
        }

        /////////////////////////////////////////////////////////////////
        // Dorks module report
        /////////////////////////////////////////////////////////////////
        if (this.gathered['dorks'] &&
            this.gathered['dorks']['result'] &&
            this.gathered['dorks']['result'].length > 3) {

            this.reportMessage = 'Dorks module...'

            let search = false;

            doc.addPage();
            doc.setFontSize(25);
            hl = 40;

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('MODULE - Dorks', 105, 23);

            // // Information table
            // if (this.gathered['dorks'] &&
            //     this.gathered['dorks']['result'] &&
            //     this.gathered['dorks']['result'][4] &&
            //     this.gathered['dorks']['result'][4]['graphic'] &&
            //     this.gathered['dorks']['result'][4]['graphic'][5] && 
            //     this.gathered['dorks']['result'][4]['graphic'][5]['searches'] &&
            //     this.gathered['dorks']['result'][4]['graphic'][5]['searches'].length > 1) {

            //     this.reportMessage = 'Dorks module...'

            //     // Image
            //     svg = this.nbCardContainer.nativeElement.querySelector('#divDorksSearches');

            //     await htmlToImage.toPng(svg)
            //       .then(function (dataUrl) {
            //         imgiKy.src = dataUrl;
            //         doc.addImage(imgiKy, 'png', 25, hl, 160, 55);
            //       })
            //       .catch(function (error) {
            //         console.error('oops, something went wrong!', error);
            //       });

            //     hl = hl + 70;

            //     search = true;
            // }

            // Information table
            if (this.gathered['dorks'] &&
                this.gathered['dorks']['result'] &&
                this.gathered['dorks']['result'][4] &&
                this.gathered['dorks']['result'][4]['graphic'] &&
                this.gathered['dorks']['result'][4]['graphic'][0] &&
                this.gathered['dorks']['result'][4]['graphic'][0]['names'] &&
                this.gathered['dorks']['result'][4]['graphic'][0]['names'].length > 0) {

                this.reportMessage = 'Dorks module...(Names)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divDorksNames');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                search = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['dorks']['result'][4]['graphic'][0]['names'];
                // list.sort((a, b)=> (a.value < b.value ? 1 : -1))

                // let a = 0;
                for (const i in list) {
                    // if (a === 16) {
                    //     break;
                    // }
                    elem = [list[i]['label']];
                    bodyTable.push(elem);
                    // a = a + 1;
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Names']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46'},
                     },
                     margin: {top: 0, left: 100},
                     // pageBreak: 'always',
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Dorks', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['dorks'] &&
                this.gathered['dorks']['result'] &&
                this.gathered['dorks']['result'][4] &&
                this.gathered['dorks']['result'][4]['graphic'] &&
                this.gathered['dorks']['result'][4]['graphic'][1] &&
                this.gathered['dorks']['result'][4]['graphic'][1]['username'] &&
                this.gathered['dorks']['result'][4]['graphic'][1]['username'].length > 0) {

                this.reportMessage = 'Dorks module...(Usernames)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divDorksUsernames');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                search = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['dorks']['result'][4]['graphic'][1]['username'];
                // list.sort((a, b)=> (a.value < b.value ? 1 : -1))

                // let a = 0;
                for (const i in list) {
                    // if (a === 16) {
                    //     break;
                    // }
                    elem = [list[i]['label']];
                    bodyTable.push(elem);
                    // a = a + 1;
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Usernames']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46'},
                     },
                     margin: {top: 0, left: 100},
                     // pageBreak: 'always',
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Dorks', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['dorks'] &&
                this.gathered['dorks']['result'] &&
                this.gathered['dorks']['result'][4] &&
                this.gathered['dorks']['result'][4]['graphic'] &&
                this.gathered['dorks']['result'][4]['graphic'][2] &&
                this.gathered['dorks']['result'][4]['graphic'][2]['social'] &&
                this.gathered['dorks']['result'][4]['graphic'][2]['social'].length > 0) {

                this.reportMessage = 'Dorks module...(Social)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divDorksSocial');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                search = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['dorks']['result'][4]['graphic'][2]['social'];
                // list.sort((a, b)=> (a.value < b.value ? 1 : -1))

                // let a = 0;
                for (const i in list) {
                    if (list[i]['title'] !== 'Social') {
                        elem = [list[i]['title'], list[i]['subtitle']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Social', 'Username']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46'},
                         1: {fillColor: '#22262a'},
                     },
                     margin: {top: 0, left: 100},
                     // pageBreak: 'always',
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Dorks', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['dorks'] &&
                this.gathered['dorks']['result'] &&
                this.gathered['dorks']['result'][4] &&
                this.gathered['dorks']['result'][4]['graphic'] &&
                this.gathered['dorks']['result'][4]['graphic'][5] &&
                this.gathered['dorks']['result'][4]['graphic'][5]['mentions'] &&
                this.gathered['dorks']['result'][4]['graphic'][5]['mentions'].length > 0) {

                this.reportMessage = 'Dorks module...(Mentions)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divDorksMentions');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                search = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['dorks']['result'][4]['graphic'][5]['mentions'];
                // list.sort((a, b)=> (a.value < b.value ? 1 : -1))

                // let a = 0;
                for (const i in list) {
                    // if (a === 16) {
                    //     break;
                    // }
                    elem = [list[i]['label']];
                    bodyTable.push(elem);
                    // a = a + 1;
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Mentions']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46'},
                     },
                     margin: {top: 0, left: 100},
                     // pageBreak: 'always',
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Dorks', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['dorks'] &&
                this.gathered['dorks']['result'] &&
                this.gathered['dorks']['result'][4] &&
                this.gathered['dorks']['result'][4]['graphic'] &&
                this.gathered['dorks']['result'][4]['graphic'][6] &&
                this.gathered['dorks']['result'][4]['graphic'][6]['hashtags'] &&
                this.gathered['dorks']['result'][4]['graphic'][6]['hashtags'].length > 0) {

                this.reportMessage = 'Dorks module...(Hashtags)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divDorksHashtag');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                search = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['dorks']['result'][4]['graphic'][6]['hashtags'];
                // list.sort((a, b)=> (a.value < b.value ? 1 : -1))

                // let a = 0;
                for (const i in list) {
                    // if (a === 16) {
                    //     break;
                    // }
                    elem = [list[i]['label']];
                    bodyTable.push(elem);
                    // a = a + 1;
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Hashtags']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46'},
                     },
                     margin: {top: 0, left: 100},
                     // pageBreak: 'always',
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Dorks', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['dorks'] &&
                this.gathered['dorks']['result'] &&
                this.gathered['dorks']['result'][4] &&
                this.gathered['dorks']['result'][4]['graphic'] &&
                this.gathered['dorks']['result'][4]['graphic'][7] &&
                this.gathered['dorks']['result'][4]['graphic'][7]['emails'] &&
                this.gathered['dorks']['result'][4]['graphic'][7]['emails'].length > 0) {

                this.reportMessage = 'Dorks module...(Emails)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divDorksEmails');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                search = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['dorks']['result'][4]['graphic'][7]['emails'];
                // list.sort((a, b)=> (a.value < b.value ? 1 : -1))

                // let a = 0;
                for (const i in list) {
                    // if (a === 16) {
                    //     break;
                    // }
                    elem = [list[i]['label']];
                    bodyTable.push(elem);
                    // a = a + 1;
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Emails']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46'},
                     },
                     margin: {top: 0, left: 100},
                     // pageBreak: 'always',
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Dorks', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['dorks'] &&
                this.gathered['dorks']['result'] &&
                this.gathered['dorks']['result'][4] &&
                this.gathered['dorks']['result'][4]['graphic'] &&
                this.gathered['dorks']['result'][4]['graphic'][4] && 
                this.gathered['dorks']['result'][4]['graphic'][4]['results'] &&
                this.gathered['dorks']['result'][4]['graphic'][4]['results'].length > 1) {

                this.reportMessage = 'Dorks module...(Analized results)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divDorksList');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 25, hl, 160, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                hl = hl + 60;

                search = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['dork']['result'][4]['graphic'][4]['results'];

                for (const i in list) {
                    // console.log(list[i]['link'], list[i]['link'].toLowerCase(), list[i]['link'].substr(0,8))
                    if (list[i]['title'].toLowerCase() !== 'searcher' && list[i]['title'].substr(0,8) !== 'Detected') {
                        elem = [list[i]['link'], list[i]['title'], list[i]['desc'], list[i]['url']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Search', 'Title', 'Description', 'URL']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 2},
                                  lineWidth: 1,
                                  fontSize: 7,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 20},
                         1: {fillColor: '#22262a', cellWidth: 40},
                         2: {fillColor: '#393f46'},
                         3: {fillColor: '#22262a', cellWidth: 40},
                        //  4: {fillColor: '#393f46'},
                     },
                     margin: {top: 0, left: 15},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            if (!search) {
                doc.setLineWidth(15);
                doc.setDrawColor('#00000');
                doc.line(20, 105, 190, 105);
                doc.line(20, 155, 190, 155);
                img.src = 'assets/images/ban.png';
                doc.addImage(img, 'png', 10, 105, 190, 50);
            }

            hl = hl + 10;
        }

        /////////////////////////////////////////////////////////////////
        // PROFILE
        /////////////////////////////////////////////////////////////////

        for (let i in this.gathered) {
            console.log("i", i)
          for (let j in this.gathered[i]) {
            for (let k in this.gathered[i][j]) {
              for (let l in this.gathered[i][j][k]) {
                if (l == "profile") {
                  for (let p in this.gathered[i][j][k][l]) {
                    this.profile.push(this.gathered[i][j][k][l][p]);
                    for (let q in this.gathered[i][j][k][l][p]) {
                      switch(q) {
                        case 'name':
                        case 'firstName':
                        case 'lastName':
                          if (this.gathered[i][j][k][l][p][q] != null) {
                              this.name.push({"label" : this.gathered[i][j][k][l][p][q], "source" : i});
                          };
                          break;
                        case 'photos':
                          for (let iphoto in this.gathered[i][j][k][l][p][q]) {
                              this.photo.push(this.gathered[i][j][k][l][p][q][iphoto]);
                          };    
                          break;
                        case 'social':
                          for (let isocial in this.gathered[i][j][k][l][p][q]) {
                              this.social.push(this.gathered[i][j][k][l][p][q][isocial]);
                          };    
                          break;
                        case 'username':
                          this.usern.push({"label" : this.gathered[i][j][k][l][p][q], "source" : i});
                          break;
                        case 'location':
                          this.location.push({"label" : this.gathered[i][j][k][l][p][q], "source" : i});
                          break;
                        case 'url':
                          this.url.push({"label" : this.gathered[i][j][k][l][p][q], "source" : i});
                          break;
                        case 'bio':
                          this.bio.push({"label" : this.gathered[i][j][k][l][p][q], "source" : i});
                          break;
                        case 'email':
                          this.emails.push({"label" : this.gathered[i][j][k][l][p][q], "source" : i});
                          break;
                        case 'phone':
                          this.phone.push({"label" : this.gathered[i][j][k][l][p][q], "source" : i});
                          break;
                        case 'geo':
                          this.geo.push({"label" : this.gathered[i][j][k][l][p][q], "source" : i});
                          break;
                        case 'organization':
                          if (Array.isArray(this.gathered[i][j][k][l][p][q])) {
                              for (let r in this.gathered[i][j][k][l][p][q]) {
                                  this.organization.push({"label" : this.gathered[i][j][k][l][p][q][r]['name'], "source" : i});
                              }

                          } else {
                              this.organization.push({"label" : this.gathered[i][j][k][l][p][q], "source" : i});
                          }    
                          break;
                        case 'gender':
                          this.gender.push({"label" : this.gathered[i][j][k][l][p][q], "source" : i});
                          break;
                        case 'presence':
                          this.presence.push({"children" : this.gathered[i][j][k][l][p][q][0]['children'],
                                              "name" : this.gathered[i][j][k][l][p][q][0]['name']
                          });
                          break;
                        default:
                          // code block
                      }
                    }
                  }
                }
              }
            }
          }
        }     

        this.reportMessage = 'Profile...'

        doc.addPage();
        doc.setFontSize(25);
        hl = 40;

        // Header title page
        img.src = 'assets/images/h1.jpg';
        doc.addImage(img, 'png', 100, 15, 100, 14);
        img.src = 'assets/images/iKy-Logo.png';
        doc.addImage(img, 'png', 185, 17, 10, 10);
        doc.setFontSize(12);
        doc.setTextColor('#05fcfc');
        doc.text('PROFILE', 105, 23);

        console.log('name', this.name);
        // Name table
        if (this.name.length > 0) {
            const bodyTable = [];
            let elem = [];
            const list = this.name;
            // Title
            // doc.setFontSize(10);
            // autoTable(doc, {
            //         head: [['Names']], body: bodyTable, headStyles: {fillColor: '#50fcfc', cellPadding: {top: 2, right: 2, bottom: 2, left: 2}, lineWidth: 1, halign: 'center', textColor: '#000000', lineColor: '#1A1A1A'}, margin: {top: 0, left: 15}, startY: hl, didDrawPage: function (data) { data.settings.margin.top = 30; }
            // });

            // hl = (doc as any).lastAutoTable.finalY + 3;

            for (const i in list) {
                elem = [list[i]['label'], list[i]['source']];
                bodyTable.push(elem);
            }

            doc.setFontSize(10);
            autoTable(doc, {
                    head: [['Name', 'Source']], body: bodyTable,
                    headStyles: {fillColor: '#50fcfc', cellPadding: {top: 2, right: 2, bottom: 2, left: 5}, lineWidth: 1, halign: 'center', textColor: '#000000', lineColor: '#1A1A1A'},
                    bodyStyles: {fillColor: '#1A1A1A', cellPadding: {top: 2, right: 2, bottom: 2, left: 2}, lineWidth: 1, fontSize: 8, textColor: '#50fcfc', lineColor: '#1A1A1A'},
                    columnStyles: {0: {fillColor: '#393f46'}, 1: {fillColor: '#22262a', halign: 'center', cellWidth: 50},},
                    margin: {top: 0, left: 15}, startY: hl,
                    didDrawPage: function (data) { data.settings.margin.top = 30; }
            });

            hl = (doc as any).lastAutoTable.finalY + 5;
        }
        // Validate pageHeight
        if ( hl + 60 > pageHeight) {
            doc.addPage();
            doc.setFontSize(25);

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('PROFILE', 105, 23);

            hl = 40;
        }

        console.log('usern', this.usern);
        // Username table
        if (this.usern.length > 0) {
            const bodyTable = [];
            let elem = [];
            const list = this.usern;

            for (const i in list) {
                elem = [list[i]['label'], list[i]['source']];
                bodyTable.push(elem);
            }

            doc.setFontSize(10);
            autoTable(doc, {
                    head: [['Username', 'Source']], body: bodyTable,
                    headStyles: {fillColor: '#50fcfc', cellPadding: {top: 2, right: 2, bottom: 2, left: 5}, lineWidth: 1, halign: 'center', textColor: '#000000', lineColor: '#1A1A1A'},
                    bodyStyles: {fillColor: '#1A1A1A', cellPadding: {top: 2, right: 2, bottom: 2, left: 2}, lineWidth: 1, fontSize: 8, textColor: '#50fcfc', lineColor: '#1A1A1A'},
                    columnStyles: {0: {fillColor: '#393f46'}, 1: {fillColor: '#22262a', halign: 'center', cellWidth: 50},},
                    margin: {top: 0, left: 15}, startY: hl,
                    didDrawPage: function (data) { data.settings.margin.top = 30; }
            });

            hl = (doc as any).lastAutoTable.finalY + 5;
        }
        // Validate pageHeight
        if ( hl + 60 > pageHeight) {
            doc.addPage();
            doc.setFontSize(25);

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('PROFILE', 105, 23);

            hl = 40;
        }

        console.log('gender', this.gender);
        // Gender table
        if (this.gender.length > 0) {
            const bodyTable = [];
            let elem = [];
            const list = this.gender;

            for (const i in list) {
                elem = [list[i]['label'], list[i]['source']];
                bodyTable.push(elem);
            }

            doc.setFontSize(10);
            autoTable(doc, {
                    head: [['Gender', 'Source']], body: bodyTable,
                    headStyles: {fillColor: '#50fcfc', cellPadding: {top: 2, right: 2, bottom: 2, left: 5}, lineWidth: 1, halign: 'center', textColor: '#000000', lineColor: '#1A1A1A'},
                    bodyStyles: {fillColor: '#1A1A1A', cellPadding: {top: 2, right: 2, bottom: 2, left: 2}, lineWidth: 1, fontSize: 8, textColor: '#50fcfc', lineColor: '#1A1A1A'},
                    columnStyles: {0: {fillColor: '#393f46'}, 1: {fillColor: '#22262a', halign: 'center', cellWidth: 50},},
                    margin: {top: 0, left: 15}, startY: hl,
                    didDrawPage: function (data) { data.settings.margin.top = 30; }
            });

            hl = (doc as any).lastAutoTable.finalY + 5;
        }
        // Validate pageHeight
        if ( hl + 60 > pageHeight) {
            doc.addPage();
            doc.setFontSize(25);

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('PROFILE', 105, 23);

            hl = 40;
        }

        console.log('email', this.emails);
        // Email table
        if (this.emails.length > 0) {
            const bodyTable = [];
            let elem = [];
            const list = this.emails;

            for (const i in list) {
                elem = [list[i]['label'], list[i]['source']];
                bodyTable.push(elem);
            }

            doc.setFontSize(10);
            autoTable(doc, {
                    head: [['Email', 'Source']], body: bodyTable,
                    headStyles: {fillColor: '#50fcfc', cellPadding: {top: 2, right: 2, bottom: 2, left: 5}, lineWidth: 1, halign: 'center', textColor: '#000000', lineColor: '#1A1A1A'},
                    bodyStyles: {fillColor: '#1A1A1A', cellPadding: {top: 2, right: 2, bottom: 2, left: 2}, lineWidth: 1, fontSize: 8, textColor: '#50fcfc', lineColor: '#1A1A1A'},
                    columnStyles: {0: {fillColor: '#393f46'}, 1: {fillColor: '#22262a', halign: 'center', cellWidth: 50},},
                    margin: {top: 0, left: 15}, startY: hl,
                    didDrawPage: function (data) { data.settings.margin.top = 30; }
            });

            hl = (doc as any).lastAutoTable.finalY + 5;
        }
        // Validate pageHeight
        if ( hl + 60 > pageHeight) {
            doc.addPage();
            doc.setFontSize(25);

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('PROFILE', 105, 23);

            hl = 40;
        }

        console.log('phone', this.phone);
        // Phone table
        if (this.phone.length > 0) {
            const bodyTable = [];
            let elem = [];
            const list = this.phone;

            for (const i in list) {
                elem = [list[i]['label'], list[i]['source']];
                bodyTable.push(elem);
            }

            doc.setFontSize(10);
            autoTable(doc, {
                    head: [['Phone', 'Source']], body: bodyTable,
                    headStyles: {fillColor: '#50fcfc', cellPadding: {top: 2, right: 2, bottom: 2, left: 5}, lineWidth: 1, halign: 'center', textColor: '#000000', lineColor: '#1A1A1A'},
                    bodyStyles: {fillColor: '#1A1A1A', cellPadding: {top: 2, right: 2, bottom: 2, left: 2}, lineWidth: 1, fontSize: 8, textColor: '#50fcfc', lineColor: '#1A1A1A'},
                    columnStyles: {0: {fillColor: '#393f46'}, 1: {fillColor: '#22262a', halign: 'center', cellWidth: 50},},
                    margin: {top: 0, left: 15}, startY: hl,
                    didDrawPage: function (data) { data.settings.margin.top = 30; }
            });

            hl = (doc as any).lastAutoTable.finalY + 5;
        }
        // Validate pageHeight
        if ( hl + 60 > pageHeight) {
            doc.addPage();
            doc.setFontSize(25);

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('PROFILE', 105, 23);

            hl = 40;
        }

        console.log('orgnization', this.organization);
        // Organization table
        if (this.organization.length > 0) {
            const bodyTable = [];
            let elem = [];
            const list = this.organization;

            for (const i in list) {
                elem = [list[i]['label'], list[i]['source']];
                bodyTable.push(elem);
            }

            doc.setFontSize(10);
            autoTable(doc, {
                    head: [['Organization', 'Source']], body: bodyTable,
                    headStyles: {fillColor: '#50fcfc', cellPadding: {top: 2, right: 2, bottom: 2, left: 5}, lineWidth: 1, halign: 'center', textColor: '#000000', lineColor: '#1A1A1A'},
                    bodyStyles: {fillColor: '#1A1A1A', cellPadding: {top: 2, right: 2, bottom: 2, left: 2}, lineWidth: 1, fontSize: 8, textColor: '#50fcfc', lineColor: '#1A1A1A'},
                    columnStyles: {0: {fillColor: '#393f46'}, 1: {fillColor: '#22262a', halign: 'center', cellWidth: 50},},
                    margin: {top: 0, left: 15}, startY: hl,
                    didDrawPage: function (data) { data.settings.margin.top = 30; }
            });

            hl = (doc as any).lastAutoTable.finalY + 5;
        }
        // Validate pageHeight
        if ( hl + 60 > pageHeight) {
            doc.addPage();
            doc.setFontSize(25);

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('PROFILE', 105, 23);

            hl = 40;
        }

        console.log('bio', this.bio);
        // Bio table
        if (this.bio.length > 0) {
            const bodyTable = [];
            let elem = [];
            const list = this.bio;

            for (const i in list) {
                elem = [list[i]['label'], list[i]['source']];
                bodyTable.push(elem);
            }

            doc.setFontSize(10);
            autoTable(doc, {
                    head: [['Bio', 'Source']], body: bodyTable,
                    headStyles: {fillColor: '#50fcfc', cellPadding: {top: 2, right: 2, bottom: 2, left: 5}, lineWidth: 1, halign: 'center', textColor: '#000000', lineColor: '#1A1A1A'},
                    bodyStyles: {fillColor: '#1A1A1A', cellPadding: {top: 2, right: 2, bottom: 2, left: 2}, lineWidth: 1, fontSize: 8, textColor: '#50fcfc', lineColor: '#1A1A1A'},
                    columnStyles: {0: {fillColor: '#393f46'}, 1: {fillColor: '#22262a', halign: 'center', cellWidth: 50},},
                    margin: {top: 0, left: 15}, startY: hl,
                    didDrawPage: function (data) { data.settings.margin.top = 30; }
            });

            hl = (doc as any).lastAutoTable.finalY + 5;
        }
        // Validate pageHeight
        if ( hl + 60 > pageHeight) {
            doc.addPage();
            doc.setFontSize(25);

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('PROFILE', 105, 23);

            hl = 40;
        }

        console.log('url', this.url);
        // URL table
        if (this.url.length > 0) {
            const bodyTable = [];
            let elem = [];
            const list = this.url;

            for (const i in list) {
                elem = [list[i]['label'], list[i]['source']];
                bodyTable.push(elem);
            }

            doc.setFontSize(10);
            autoTable(doc, {
                    head: [['URL', 'Source']], body: bodyTable,
                    headStyles: {fillColor: '#50fcfc', cellPadding: {top: 2, right: 2, bottom: 2, left: 5}, lineWidth: 1, halign: 'center', textColor: '#000000', lineColor: '#1A1A1A'},
                    bodyStyles: {fillColor: '#1A1A1A', cellPadding: {top: 2, right: 2, bottom: 2, left: 2}, lineWidth: 1, fontSize: 8, textColor: '#50fcfc', lineColor: '#1A1A1A'},
                    columnStyles: {0: {fillColor: '#393f46'}, 1: {fillColor: '#22262a', halign: 'center', cellWidth: 50},},
                    margin: {top: 0, left: 15}, startY: hl,
                    didDrawPage: function (data) { data.settings.margin.top = 30; }
            });

            hl = (doc as any).lastAutoTable.finalY + 5;
        }
        // Validate pageHeight
        if ( hl + 60 > pageHeight) {
            doc.addPage();
            doc.setFontSize(25);

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('PROFILE', 105, 23);

            hl = 40;
        }

        console.log('social', this.social);
        // Social table
        if (this.social.length > 0) {
            const bodyTable = [];
            let elem = [];
            const list = this.social;

            for (const i in list) {
                elem = [list[i]['name'], list[i]['url'], list[i]['source']];
                bodyTable.push(elem);
            }

            doc.setFontSize(10);
            autoTable(doc, {
                    head: [['Social Network', 'URL', 'Source']], body: bodyTable,
                    headStyles: {fillColor: '#50fcfc', cellPadding: {top: 2, right: 2, bottom: 2, left: 5}, lineWidth: 1, halign: 'center', textColor: '#000000', lineColor: '#1A1A1A'},
                    bodyStyles: {fillColor: '#1A1A1A', cellPadding: {top: 2, right: 2, bottom: 2, left: 2}, lineWidth: 1, fontSize: 8, textColor: '#50fcfc', lineColor: '#1A1A1A'},
                    columnStyles: {0: {fillColor: '#393f46'}, 1: {fillColor: '#22262a'}, 2: {fillColor: '#393f46', halign: 'center', cellWidth: 50},},
                    margin: {top: 0, left: 15}, startY: hl,
                    didDrawPage: function (data) { data.settings.margin.top = 30; }
            });

            hl = (doc as any).lastAutoTable.finalY + 5;
        }
        // Validate pageHeight
        if ( hl + 60 > pageHeight) {
            doc.addPage();
            doc.setFontSize(25);

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('PROFILE', 105, 23);

            hl = 40;
        }

        console.log('photo', this.photo);
        /////////////////////////////////////////////////////////////////
        // TODO : Photos
        /////////////////////////////////////////////////////////////////

        console.log('location', this.location);
        // Location table
        if (this.location.length > 0) {
            const bodyTable = [];
            let elem = [];
            const list = this.location;

            for (const i in list) {
                elem = [list[i]['label'], list[i]['source']];
                bodyTable.push(elem);
            }

            doc.setFontSize(10);
            autoTable(doc, {
                    head: [['Location', 'Source']], body: bodyTable,
                    headStyles: {fillColor: '#50fcfc', cellPadding: {top: 2, right: 2, bottom: 2, left: 5}, lineWidth: 1, halign: 'center', textColor: '#000000', lineColor: '#1A1A1A'},
                    bodyStyles: {fillColor: '#1A1A1A', cellPadding: {top: 2, right: 2, bottom: 2, left: 2}, lineWidth: 1, fontSize: 8, textColor: '#50fcfc', lineColor: '#1A1A1A'},
                    columnStyles: {0: {fillColor: '#393f46'}, 1: {fillColor: '#22262a', halign: 'center', cellWidth: 50},},
                    margin: {top: 0, left: 15}, startY: hl,
                    didDrawPage: function (data) { data.settings.margin.top = 30; }
            });

            hl = (doc as any).lastAutoTable.finalY + 5;
        }
        // Validate pageHeight
        if ( hl + 60 > pageHeight) {
            doc.addPage();
            doc.setFontSize(25);

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('PROFILE', 105, 23);

            hl = 40;
        }

        console.log('geo', this.geo);
        // Geo table
        if (this.geo.length > 0) {
            const bodyTable = [];
            let elem = [];
            const list = this.geo;

            for (const i in list) {
                elem = [list[i]['label']['Name'], list[i]['label']['Longitude'], list[i]['label']['Latitude'], list[i]['source']];
                bodyTable.push(elem);
            }

            doc.setFontSize(10);
            autoTable(doc, {
                    head: [['Location', 'Longitude', 'Latitude', 'Source']], body: bodyTable,
                    headStyles: {fillColor: '#50fcfc', cellPadding: {top: 2, right: 2, bottom: 2, left: 5}, lineWidth: 1, halign: 'center', textColor: '#000000', lineColor: '#1A1A1A'},
                    bodyStyles: {fillColor: '#1A1A1A', cellPadding: {top: 2, right: 2, bottom: 2, left: 2}, lineWidth: 1, fontSize: 8, textColor: '#50fcfc', lineColor: '#1A1A1A'},
                    columnStyles: {0: {fillColor: '#393f46'}, 1: {fillColor: '#22262a', halign: 'center'}, 2: {fillColor: '#393f46', halign: 'center'}, 3: {fillColor: '#22262a', halign: 'center', cellWidth: 50},},
                    margin: {top: 0, left: 15}, startY: hl,
                    didDrawPage: function (data) { data.settings.margin.top = 30; }
            });

            hl = (doc as any).lastAutoTable.finalY + 5;
        }
        // // Validate pageHeight
        // if ( hl + 60 > pageHeight) {
        //     doc.addPage();
        //     doc.setFontSize(25);

        //     // Header title page
        //     img.src = 'assets/images/h1.jpg';
        //     doc.addImage(img, 'png', 100, 15, 100, 14);
        //     img.src = 'assets/images/iKy-Logo.png';
        //     doc.addImage(img, 'png', 185, 17, 10, 10);
        //     doc.setFontSize(12);
        //     doc.setTextColor('#05fcfc');
        //     doc.text('PROFILE', 105, 23);

        //     hl = 40;
        // }
        // TODO : Activate it when include Presence

        console.log('presence', this.presence);

        /////////////////////////////////////////////////////////////////
        // TIMELINE
        /////////////////////////////////////////////////////////////////

        for (let i in this.gathered) {
          for (let j in this.gathered[i]) {
            for (let k in this.gathered[i][j]) {
              for (let l in this.gathered[i][j][k]) {
                if (l == "timeline") {
                  for (let t in this.gathered[i][j][k][l]) {
                    this.timeline.push(this.gathered[i][j][k][l][t]);
                  }
                }
              }
            }
          }
        }     
    
        // TODO : Normalize dates
        this.timeline.sort(function(a, b){
            var dateA=a.date.toLowerCase(), dateB=b.date.toLowerCase()
            if (dateA > dateB) //sort string ascending
                return -1 
            if (dateA < dateB)
                return 1
            return 0 
        })
    
        console.log('Report Timeline', this.timeline);
        this.reportMessage = 'Timeline...'

        doc.addPage();
        doc.setFontSize(25);
        hl = 40;

        // Header title page
        img.src = 'assets/images/h1.jpg';
        doc.addImage(img, 'png', 100, 15, 100, 14);
        img.src = 'assets/images/iKy-Logo.png';
        doc.addImage(img, 'png', 185, 17, 10, 10);
        doc.setFontSize(12);
        doc.setTextColor('#05fcfc');
        doc.text('TIMELINE', 105, 23);

        for (let i in this.timeline) {
            hl = hl + 5;
            doc.setFillColor('#05fcfc');
            doc.setDrawColor('#05fcfc');
            doc.circle(50, hl + 10, 2, 'F');

            // Information table
            let headTable = [[this.timeline[i]['date']]];
            let bodyTable = [[this.timeline[i]['action'] + ' - ' + [this.timeline[i]['desc']]]];
    
            autoTable(doc, {
                head: headTable,
                body: bodyTable,
                margin: {left: 60, right: 40},
                showHead: true,
                headStyles: {fillColor: '#50fcfc', cellPadding: {top: 2, right: 2, bottom: 2, left: 2}, lineWidth: 1, halign: 'left', textColor: '#000000', lineColor: '#1A1A1A'},
                bodyStyles: {fillColor: '#1A1A1A', cellPadding: {top: 2, right: 2, bottom: 2, left: 2}, lineWidth: 1, fontSize: 8, textColor: '#50fcfc', lineColor: '#1A1A1A'},
                columnStyles: {0: {fillColor: '#393f46'},},
                startY: hl + 10,
            });

            doc.setFillColor('#05fcfc');
            doc.setDrawColor('#05fcfc');
            doc.line(50, hl, 50, (doc as any).lastAutoTable.finalY + 5);
            hl = (doc as any).lastAutoTable.finalY;

            // Validate pageHeight
            if ( hl + 50 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('TIMELINE', 105, 23);

                hl = 40;
            }
        }
    
        /////////////////////////////////////////////////////////////////
        // END
        /////////////////////////////////////////////////////////////////
        this.reportEnd = true;
        this.reportMessage = 'Report DONE';

        this.report = doc;
        // doc.save('Report_iKy_' + Date.now() + '.pdf');
        this.processing = false;
    }

  cancelDownload(doc: any) {
    console.log('Cerrame la 9');
    doc.save('Report_iKy_' + Date.now() + '.pdf');
  }

}
