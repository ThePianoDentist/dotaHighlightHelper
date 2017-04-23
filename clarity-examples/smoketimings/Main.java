package skadistats.clarity.examples.smoketimings;

import org.joda.time.format.PeriodFormatter;
import org.joda.time.format.PeriodFormatterBuilder;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import skadistats.clarity.decoder.Util;
import skadistats.clarity.event.Insert;
import skadistats.clarity.model.CombatLogEntry;
import skadistats.clarity.model.Entity;
import skadistats.clarity.model.FieldPath;
import skadistats.clarity.processor.entities.UsesEntities;
import skadistats.clarity.processor.gameevents.OnCombatLogEntry;
import skadistats.clarity.processor.runner.Context;
import skadistats.clarity.processor.runner.SimpleRunner;
import skadistats.clarity.source.MappedFileSource;

import java.io.IOException;
import java.util.ArrayList;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@UsesEntities
public class Main {

    private static final Logger log = LoggerFactory.getLogger(Main.class.getPackage().getClass());
    public static final Pattern ID_DOT_DEM = Pattern.compile("(\\d+).DEM", Pattern.CASE_INSENSITIVE);

    @Insert
    private Context ctx;
    private long matchID;

    private long compileMatchID(String filename){
        Matcher matcher = ID_DOT_DEM.matcher(filename);
        if (matcher.find()) {
            return Long.parseLong(matcher.group(1));
        }
        throw new NumberFormatException("No match ID at end of filename: " + filename);
    }

    private String compileName(String attackerName, boolean isIllusion) {
        return attackerName != null ? attackerName + (isIllusion ? " (illusion)" : "") : "UNKNOWN";
    }

    private String getAttackerNameCompiled(CombatLogEntry cle) {
        return compileName(cle.getAttackerName(), cle.isAttackerIllusion());
    }

    private String getTargetNameCompiled(CombatLogEntry cle) {
        return compileName(cle.getTargetName(), cle.isTargetIllusion());
    }

    @OnCombatLogEntry
    public void onCombatLogEntry(CombatLogEntry cle) {
        String time = "(" + this.matchID + ")[" + ctx.getTick() + "]";
        switch (cle.getType()) {
            case DOTA_COMBATLOG_ITEM:
                if (cle.getInflictorName().equals("item_smoke_of_deceit")) {
                    log.info("{} {} uses {}",
                            time,
                            getAttackerNameCompiled(cle),
                            cle.getInflictorName()
                    );
                }
                break;
            case DOTA_COMBATLOG_MODIFIER_ADD:
                if (cle.getInflictorName().equals("modifier_smoke_of_deceit")) {
                    log.info("{} {} receives {} buff/debuff from {}",
                            time,
                            getTargetNameCompiled(cle),
                            cle.getInflictorName(),
                            getAttackerNameCompiled(cle)
                    );
                }
                break;
            case DOTA_COMBATLOG_MODIFIER_REMOVE:
                if (cle.getInflictorName().equals("modifier_smoke_of_deceit")) {
                    log.info("{} {} loses {} buff/debuff",
                            time,
                            getTargetNameCompiled(cle),
                            cle.getInflictorName()
                    );
                }
                break;

            default:
                break;

        }
    }

    public void run(String filename) throws IOException {
        this.matchID = compileMatchID(filename);
        long tStart = System.currentTimeMillis();
        new SimpleRunner(new MappedFileSource(filename)).runWith(this);
        long tMatch = System.currentTimeMillis() - tStart;
        log.info("total time taken: {}s", (tMatch) / 1000.0);
    }

    public static void main(String[] args) throws Exception {
        ExecutorService executor = Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors() + 1);

        ArrayList<Callable<Void>> tasks = new ArrayList<>(args.length);

        for (final String file : args) {
            //new Main().run(file);
            tasks.add(new Callable<Void>() {
                public Void call(){
                    try {
                        new Main().run(file);
                    }
                    catch (IOException e) {
                        System.err.println("Could not find/read file: " + file);
                        e.printStackTrace();
                    }
                    return null;
                }
            });
        }
        executor.invokeAll(tasks, 20, TimeUnit.MINUTES);
        executor.shutdown();
    }

}
