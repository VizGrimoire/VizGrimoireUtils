#/bin/bash

# Change to the directory where source code projects directories are
PROJECTS_SCM=/home/owl/Automator/tests/SingleProject
PWD=`pwd`
# Name of database, mysql server is accessed using root user without password.
DB=cp_cvsanaly_PolarsysMaturity
LOG=/tmp/clocer.log

echo "Running clocer for ${PROJECTS_SCM}. Look to ${LOG} to see the progress."
echo $(cat <<EOF
DROP TABLE IF exists t, metadata;
create table metadata (
                timestamp text,    
                Project   text,    
                elapsed_s real);   
create table t        (
                Project   text   ,  
                Language  text   ,  
                File      text   ,  
                nBlank    integer,  
                nComment  integer,  
                nCode     integer,  
                nScaled   real   );
EOF
) | mysql -u root ${DB}
cd "${PROJECTS_SCM}" 
time ls -1 | awk '{print "cloc " $1 " --sql-project=\""$1"\" --sql-append --sql /tmp/" $1 ".sql && replace \"begin transaction\" \"start transaction\" -- /tmp/" $1 ".sql && mysql -u root '${DB}' < /tmp/"$1".sql"}' | sh > "${LOG}" 
cd "${PWD}" 
echo $(cat <<EOF
alter table metadata add total_sloc INT(11);
update metadata m, (select Project, sum(nCode) as sum_sloc from t group by Project) t set m.total_sloc = t.sum_sloc where m.Project = t.Project;
EOF
) | mysql -u root ${DB}
echo "clocer finished. The data should be in ${DB}"
